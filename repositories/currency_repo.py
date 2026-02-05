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
from config import EGCURRENCY_URL, HEADERS, REQUEST_TIMEOUT
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
        except (requests.exceptions.RequestException, ValueError):
            pass
        
        # Fallback: Return approximate market rate
        return UsdVndRate(
            sell_rate=Decimal('25500'),
            source="Fallback (Scraping Failed)",
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
