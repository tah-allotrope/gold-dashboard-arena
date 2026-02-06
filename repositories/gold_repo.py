<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/gold_repo.py
"""
Gold price repository for Vietnam Gold Dashboard.
Fetches SJC gold prices with Mi Hồng fallback.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional
from decimal import Decimal

from .base import Repository
from models import GoldPrice
from config import SJC_URL, MIHONG_URL, HEADERS, REQUEST_TIMEOUT
from utils import cached, sanitize_vn_number


class GoldRepository(Repository[GoldPrice]):
    """
    Repository for Vietnamese gold prices.
    
    Strategy:
    1. Try SJC primary source with strict headers
    2. If SJC fails (timeout, 404, blocked), fallback to Mi Hồng
    3. If both fail, return approximate market data
    4. Cache results to avoid rapid retries
    """
    
    @cached
    def fetch(self) -> GoldPrice:
        """
        Fetch current gold price from SJC or Mi Hồng.
        
        Returns:
            GoldPrice model with validated data
            
        Note:
            Returns fallback data if all sources fail to ensure UI stability
        """
        try:
            return self._fetch_from_sjc()
        except (requests.exceptions.RequestException, ValueError):
            pass
        
        try:
            return self._fetch_from_mihong()
        except (requests.exceptions.RequestException, ValueError):
            pass
        
        # Fallback: Return approximate market data
        # Note: This is a fallback when scraping fails. SJC gold typically trades
        # at 85-90 million VND/tael for buy, 86-91 million VND/tael for sell
        return GoldPrice(
            buy_price=Decimal('87500000'),
            sell_price=Decimal('88500000'),
            unit="VND/tael",
            source="Fallback (Scraping Failed)",
            timestamp=datetime.now()
        )
    
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
            timeout=REQUEST_TIMEOUT,
            verify=False
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
    
    def _extract_sjc_price(self, soup: BeautifulSoup, price_type: str) -> Optional[float]:
        """
        Extract buy/sell price from SJC HTML.
        SJC loads prices via JavaScript, so table is empty in initial HTML.
        Return None to trigger Mi Hồng fallback.
        """
        return None
    
    def _extract_mihong_price(self, soup: BeautifulSoup, price_type: str) -> Optional[float]:
        """
        Extract buy/sell price from Mi Hồng HTML.
        Look for price sections with SJC gold type.
        """
        # Try table-based extraction first
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                cell_texts = [cell.get_text(strip=True) for cell in cells]
                
                # Look for row containing SJC
                if any('SJC' in text for text in cell_texts):
                    # Try to find buy/sell prices in this row
                    for i, text in enumerate(cell_texts):
                        if 'buy' in price_type.lower():
                            # Buy price typically in column 1 or 2
                            if i > 0 and i < len(cell_texts):
                                price_val = sanitize_vn_number(cell_texts[i])
                                if price_val and price_val > 1000000:
                                    return price_val
                        elif 'sell' in price_type.lower():
                            # Sell price typically in column 2 or 3
                            if i > 1 and i < len(cell_texts):
                                price_val = sanitize_vn_number(cell_texts[i])
                                if price_val and price_val > 1000000:
                                    return price_val
        
        # Fallback to text-based extraction
        text = soup.get_text()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        for i, line in enumerate(lines):
            if 'SJC' in line:
                # Look ahead for buy/sell indicators and prices
                for j in range(i, min(len(lines), i+15)):
                    candidate = lines[j]
                    
                    # Check for buy/sell keywords (English and Vietnamese)
                    is_buy_line = any(keyword in candidate.lower() for keyword in ['buy', 'mua', 'buying'])
                    is_sell_line = any(keyword in candidate.lower() for keyword in ['sell', 'bán', 'selling'])
                    
                    if (price_type.lower() == 'buy' and is_buy_line) or (price_type.lower() == 'sell' and is_sell_line):
                        # Look for price in this line and next few lines
                        for k in range(j, min(len(lines), j+5)):
                            price_val = sanitize_vn_number(lines[k])
                            if price_val and price_val > 1000000 and price_val < 100000000:
                                return price_val
        
        return None
=======
"""
Gold price repository for Vietnam Gold Dashboard.
Fetches SJC gold prices with Mi Hồng fallback.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional
from decimal import Decimal

from .base import Repository
from models import GoldPrice
from config import SJC_URL, MIHONG_URL, DOJI_API_URL, HEADERS, REQUEST_TIMEOUT
from utils import cached, sanitize_vn_number


class GoldRepository(Repository[GoldPrice]):
    """
    Repository for Vietnamese gold prices.
    
    Strategy:
    1. Try SJC primary source with strict headers
    2. If SJC fails (timeout, 404, blocked), fallback to Mi Hồng
    3. If both fail, return approximate market data
    4. Cache results to avoid rapid retries
    """
    
    @cached
    def fetch(self) -> GoldPrice:
        """
        Fetch current gold price from DOJI API, Mi Hồng, or SJC.
        
        Returns:
            GoldPrice model with validated data
            
        Note:
            Returns fallback data if all sources fail to ensure UI stability
        """
        try:
            return self._fetch_from_doji()
        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"DOJI fetch failed: {e}")
        
        try:
            return self._fetch_from_mihong()
        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"Mi Hồng fetch failed: {e}")
        
        try:
            return self._fetch_from_sjc()
        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"SJC fetch failed: {e}")
        
        return GoldPrice(
            buy_price=Decimal('175400000'),
            sell_price=Decimal('175400000'),
            unit="VND/tael",
            source="Fallback (Scraping Failed)",
            timestamp=datetime.now()
        )
    
    def _fetch_from_doji(self) -> GoldPrice:
        """
        Fetch gold price from DOJI API (primary source).
        
        DOJI returns XML with prices in units of 10,000 VND.
        E.g., Sell='17,540' means 175,400,000 VND/tael.
        """
        response = requests.get(
            DOJI_API_URL,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml-xml')
        
        dgp_list = soup.find('DGPlist')
        if not dgp_list:
            raise ValueError("No DGPlist found in DOJI response")
        
        buy_price = None
        sell_price = None
        
        for row in dgp_list.find_all('Row'):
            name = row.get('Name', '')
            if 'HCM' in name and 'lẻ' in name.lower():
                sell_str = row.get('Sell', '').replace(',', '')
                buy_str = row.get('Buy', '').replace(',', '')
                
                try:
                    sell_val = Decimal(sell_str)
                    buy_val = Decimal(buy_str)
                    
                    if sell_val > 1000:
                        sell_price = sell_val * Decimal('10000')
                    if buy_val > 1000:
                        buy_price = buy_val * Decimal('10000')
                except:
                    pass
                break
        
        if not buy_price or not sell_price:
            for row in dgp_list.find_all('Row'):
                name = row.get('Name', '')
                if 'HCM' in name:
                    sell_str = row.get('Sell', '').replace(',', '')
                    buy_str = row.get('Buy', '').replace(',', '')
                    
                    try:
                        sell_val = Decimal(sell_str)
                        buy_val = Decimal(buy_str)
                        
                        if sell_val > 1000:
                            sell_price = sell_val * Decimal('10000')
                        if buy_val > 1000:
                            buy_price = buy_val * Decimal('10000')
                    except:
                        pass
                    break
        
        if not buy_price or not sell_price:
            raise ValueError("Failed to parse DOJI gold prices")
        
        return GoldPrice(
            buy_price=buy_price,
            sell_price=sell_price,
            unit="VND/tael",
            source="DOJI",
            timestamp=datetime.now()
        )
    
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
            timeout=REQUEST_TIMEOUT,
            verify=False
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
    
    def _extract_sjc_price(self, soup: BeautifulSoup, price_type: str) -> Optional[float]:
        """
        Extract buy/sell price from SJC HTML.
        SJC loads prices via JavaScript, so table is empty in initial HTML.
        Return None to trigger Mi Hồng fallback.
        """
        return None
    
    def _extract_mihong_price(self, soup: BeautifulSoup, price_type: str) -> Optional[float]:
        """
        Extract buy/sell price from Mi Hồng HTML.
        Look for price sections with SJC gold type.
        """
        # Try table-based extraction first
        tables = soup.find_all('table')
        for table in tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                cell_texts = [cell.get_text(strip=True) for cell in cells]
                
                # Look for row containing SJC
                if any('SJC' in text for text in cell_texts):
                    # Try to find buy/sell prices in this row
                    for i, text in enumerate(cell_texts):
                        if 'buy' in price_type.lower():
                            # Buy price typically in column 1 or 2
                            if i > 0 and i < len(cell_texts):
                                price_val = sanitize_vn_number(cell_texts[i])
                                if price_val and price_val > 1000000:
                                    return price_val
                        elif 'sell' in price_type.lower():
                            # Sell price typically in column 2 or 3
                            if i > 1 and i < len(cell_texts):
                                price_val = sanitize_vn_number(cell_texts[i])
                                if price_val and price_val > 1000000:
                                    return price_val
        
        # Fallback to text-based extraction
        text = soup.get_text()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        for i, line in enumerate(lines):
            if 'SJC' in line:
                # Look ahead for buy/sell indicators and prices
                for j in range(i, min(len(lines), i+15)):
                    candidate = lines[j]
                    
                    # Check for buy/sell keywords (English and Vietnamese)
                    is_buy_line = any(keyword in candidate.lower() for keyword in ['buy', 'mua', 'buying'])
                    is_sell_line = any(keyword in candidate.lower() for keyword in ['sell', 'bán', 'selling'])
                    
                    if (price_type.lower() == 'buy' and is_buy_line) or (price_type.lower() == 'sell' and is_sell_line):
                        # Look for price in this line and next few lines
                        for k in range(j, min(len(lines), j+5)):
                            price_val = sanitize_vn_number(lines[k])
                            if price_val and price_val > 1000000 and price_val < 100000000:
                                return price_val
        
        return None
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-64c9d6fe/repositories/gold_repo.py
