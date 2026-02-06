"""
Currency exchange repository for Vietnam Gold Dashboard.
Fetches USD/VND black market rates from EGCurrency with fallback.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional
from decimal import Decimal

from .base import Repository
from models import UsdVndRate
from config import EGCURRENCY_URL, CHOGIA_AJAX_URL, HEADERS, REQUEST_TIMEOUT
from utils import cached, sanitize_vn_number


class CurrencyRepository(Repository[UsdVndRate]):
    """
    Repository for USD/VND black market exchange rates.
    
    Source: EGCurrency black market page
    Extracts the sell price for USD to VND conversion.
    """
    
    @cached
    def fetch(self) -> UsdVndRate:
        """
        Fetch current USD/VND black market rate with fallback.
        
        Returns:
            UsdVndRate model with validated data or fallback approximate rate
        """
        try:
            return self._fetch_from_chogia()
        except (requests.exceptions.RequestException, ValueError, KeyError) as e:
            print(f"chogia.vn fetch failed: {e}")
        
        try:
            response = requests.get(
                EGCURRENCY_URL,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            sell_rate = self._extract_sell_rate(soup)
            
            if sell_rate:
                return UsdVndRate(
                    sell_rate=sell_rate,
                    source="EGCurrency",
                    timestamp=datetime.now()
                )
        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"EGCurrency fetch failed: {e}")
        
        return UsdVndRate(
            sell_rate=Decimal('26500'),
            source="Fallback (Scraping Failed)",
            timestamp=datetime.now()
        )
    
    def _fetch_from_chogia(self) -> UsdVndRate:
        """
        Fetch USD black market rate from chogia.vn AJAX endpoint (primary source).
        
        POST to WordPress admin-ajax with action=load_gia_ngoai_te_cho_do_thi&ma=USD
        Returns JSON with daily rates; we take the latest entry.
        """
        response = requests.post(
            CHOGIA_AJAX_URL,
            headers={
                **HEADERS,
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            data={
                'action': 'load_gia_ngoai_te_cho_do_thi',
                'ma': 'USD'
            },
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        
        data = response.json()
        
        if not data.get('success') or not data.get('data'):
            raise ValueError("chogia.vn returned unsuccessful response")
        
        entries = data['data']
        if not entries:
            raise ValueError("No USD rate entries in chogia.vn response")
        
        latest = entries[-1]
        
        sell_rate_str = latest.get('gia_ban', '')
        sell_rate = Decimal(sell_rate_str)
        
        if sell_rate < 20000 or sell_rate > 35000:
            raise ValueError(f"USD rate {sell_rate} outside expected range")
        
        return UsdVndRate(
            sell_rate=sell_rate,
            source="chogia.vn",
            timestamp=datetime.now()
        )
    
    def _extract_sell_rate(self, soup: BeautifulSoup) -> Optional[Decimal]:
        """
        Extract sell rate from EGCurrency HTML.
        
        Targets "Sell Price" text and applies Vietnamese number sanitization.
        """
        text = soup.get_text()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in ['sell', 'bán', 'selling', 'sell price']):
                for j in range(i, min(len(lines), i + 5)):
                    rate = sanitize_vn_number(lines[j])
                    if rate and 20000 < rate < 30000:
                        return rate
        
        price_elements = soup.find_all(['div', 'span', 'td', 'p'], class_=lambda x: x and any(
            keyword in str(x).lower() for keyword in ['price', 'rate', 'sell']
        ))
        
        for elem in price_elements:
            elem_text = elem.get_text(strip=True)
            rate = sanitize_vn_number(elem_text)
            if rate and 20000 < rate < 30000:
                return rate
        
        import re
        numbers = re.findall(r'\d{1,3}(?:[.,]\d{3})+(?:[.,]\d{1,2})?', text)
        for num_str in numbers:
            rate = sanitize_vn_number(num_str)
            if rate and 20000 < rate < 30000:
                return rate
        
        return None
