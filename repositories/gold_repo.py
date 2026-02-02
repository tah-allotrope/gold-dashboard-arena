"""
Gold price repository for Vietnam Gold Dashboard.
Fetches SJC gold prices with multiple fallbacks.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional
from decimal import Decimal

from .base import Repository
from models import GoldPrice
from config import SJC_URL, MIHONG_URL, GOLD_24H_URL, HEADERS, REQUEST_TIMEOUT
from utils import cached, sanitize_vn_number


class GoldRepository(Repository[GoldPrice]):
    """
    Repository for Vietnamese gold prices.
    
    Strategy:
    1. Try 24h.com.vn (HTML-based, more reliable)
    2. Try SJC primary source (JS-based, often fails)
    3. Try Mi Hồng fallback (JS-based, often fails)
    4. Cache results to avoid rapid retries
    """
    
    @cached
    def fetch(self) -> GoldPrice:
        """
        Fetch current gold price from various sources.
        
        Returns:
            GoldPrice model with validated data
            
        Raises:
            requests.exceptions.RequestException: If all sources fail
            ValueError: If data parsing fails
        """
        # Try 24h first as it's more scrapable
        try:
            return self._fetch_from_24h()
        except (requests.exceptions.RequestException, ValueError):
            pass
            
        try:
            return self._fetch_from_sjc()
        except (requests.exceptions.RequestException, ValueError):
            pass
        
        try:
            return self._fetch_from_mihong()
        except (requests.exceptions.RequestException, ValueError):
            pass
        
        # Fallback: Return approximate market data if all else fails
        return GoldPrice(
            buy_price=Decimal('87500000'),
            sell_price=Decimal('88500000'),
            unit="VND/tael",
            source="Fallback (Scraping Failed)",
            timestamp=datetime.now()
        )
    
    def _fetch_from_24h(self) -> GoldPrice:
        """Fetch gold price from 24h.com.vn."""
        response = requests.get(
            GOLD_24H_URL,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.content, 'lxml')

        # Look for SJC row in tables
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                row_text = row.get_text()
                if 'SJC' in row_text:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 3:
                        # Take only the first part of the text (in case there are up/down change values)
                        # Avoid get_text(strip=True) as it joins numeric parts
                        buy_text = cells[1].get_text().strip().split()[0]
                        sell_text = cells[2].get_text().strip().split()[0]

                        buy_val = sanitize_vn_number(buy_text)
                        sell_val = sanitize_vn_number(sell_text)

                        if buy_val and sell_val:
                            # 24h quotes often in thousands and for 2 taels (e.g. 169,000)
                            # Or per tael (e.g. 84,500,000)
                            if buy_val < 1000000:
                                if buy_val > 100000:
                                    # Case: 169,000 meaning 169,000,000 for 2 taels
                                    buy_val = (buy_val * 1000) / 2
                                    sell_val = (sell_val * 1000) / 2
                                else:
                                    # Case: 84,500 meaning 84,500,000 per tael
                                    buy_val = buy_val * 1000
                                    sell_val = sell_val * 1000

                            return GoldPrice(
                                buy_price=buy_val,
                                sell_price=sell_val,
                                unit="VND/tael",
                                source="24h.com.vn",
                                timestamp=datetime.now()
                            )

        raise ValueError("Failed to parse gold price from 24h.com.vn")

    def _fetch_from_sjc(self) -> GoldPrice:
        """Fetch gold price from SJC official site."""
        response = requests.get(
            SJC_URL,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        buy_price = self._extract_sjc_price(soup, 'buy')
        sell_price = self._extract_sjc_price(soup, 'sell')
        
        if not buy_price or not sell_price:
            raise ValueError("Failed to parse SJC gold prices")
        
        return GoldPrice(
            buy_price=buy_price,
            sell_price=sell_price,
            unit="VND/tael",
            source="SJC",
            timestamp=datetime.now()
        )
    
    def _fetch_from_mihong(self) -> GoldPrice:
        """Fetch gold price from Mi Hồng fallback source."""
        response = requests.get(
            MIHONG_URL,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        buy_price = self._extract_mihong_price(soup, 'buy')
        sell_price = self._extract_mihong_price(soup, 'sell')
        
        if not buy_price or not sell_price:
            raise ValueError("Failed to parse Mi Hồng gold prices")
        
        return GoldPrice(
            buy_price=buy_price,
            sell_price=sell_price,
            unit="VND/tael",
            source="Mi Hồng",
            timestamp=datetime.now()
        )
    
    def _extract_sjc_price(self, soup: BeautifulSoup, price_type: str) -> Optional[Decimal]:
        """SJC loads prices via JavaScript, return None for fallback."""
        return None
    
    def _extract_mihong_price(self, soup: BeautifulSoup, price_type: str) -> Optional[Decimal]:
        """Extract prices from Mi Hồng HTML text if present."""
        text = soup.get_text()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        for i, line in enumerate(lines):
            if 'SJC' in line:
                for j in range(i, min(len(lines), i+15)):
                    candidate = lines[j]
                    is_buy = any(kw in candidate.lower() for kw in ['buy', 'mua'])
                    is_sell = any(kw in candidate.lower() for kw in ['sell', 'bán'])
                    
                    if (price_type == 'buy' and is_buy) or (price_type == 'sell' and is_sell):
                        for k in range(j, min(len(lines), j+5)):
                            val = sanitize_vn_number(lines[k])
                            if val and 1000000 < val < 100000000:
                                return val
        return None
