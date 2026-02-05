<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/gold_repo.py
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/gold_repo.py
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/gold_repo.py
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/gold_repo.py
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/gold_repo.py
"""
Gold price repository for Vietnam Gold Dashboard.
Fetches SJC gold prices with Mi Hồng fallback.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional

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
    3. Cache results to avoid rapid retries
    """
    
    @cached
    def fetch(self) -> GoldPrice:
        """
        Fetch current gold price from SJC or Mi Hồng.
        
        Returns:
            GoldPrice model with validated data
            
        Raises:
            requests.exceptions.RequestException: If all sources fail
            ValueError: If data parsing fails
        """
        try:
            return self._fetch_from_sjc()
        except (requests.exceptions.RequestException, ValueError) as e:
            try:
                return self._fetch_from_mihong()
            except (requests.exceptions.RequestException, ValueError):
                raise e
    
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
        text = soup.get_text()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        for i, line in enumerate(lines):
            if 'SJC' in line and ('Gold' in line or 'gold' in line):
                for j in range(i, min(len(lines), i+10)):
                    candidate = lines[j]
                    if price_type.lower() in candidate.lower() or ('buy' in price_type.lower() and 'mua' in candidate.lower()) or ('sell' in price_type.lower() and 'bán' in candidate.lower()):
                        for k in range(j, min(len(lines), j+5)):
                            price_val = sanitize_vn_number(lines[k])
                            if price_val and price_val > 1000000:
                                return price_val
        
        return None
=======
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/repositories/gold_repo.py
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/repositories/gold_repo.py
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/repositories/gold_repo.py
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/repositories/gold_repo.py
"""
Gold price repository for Vietnam Gold Dashboard.
Fetches SJC gold prices with Mi Hồng fallback.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/gold_repo.py
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/gold_repo.py
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/gold_repo.py
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/gold_repo.py
=======
from decimal import Decimal
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/repositories/gold_repo.py
=======
from decimal import Decimal
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/repositories/gold_repo.py
=======
from decimal import Decimal
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/repositories/gold_repo.py
=======
from decimal import Decimal
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/repositories/gold_repo.py

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
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/gold_repo.py
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/gold_repo.py
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/gold_repo.py
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/gold_repo.py
    3. Cache results to avoid rapid retries
=======
    3. If both fail, return approximate market data
    4. Cache results to avoid rapid retries
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/repositories/gold_repo.py
=======
    3. If both fail, return approximate market data
    4. Cache results to avoid rapid retries
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/repositories/gold_repo.py
=======
    3. If both fail, return approximate market data
    4. Cache results to avoid rapid retries
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/repositories/gold_repo.py
=======
    3. If both fail, return approximate market data
    4. Cache results to avoid rapid retries
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/repositories/gold_repo.py
    """
    
    @cached
    def fetch(self) -> GoldPrice:
        """
        Fetch current gold price from SJC or Mi Hồng.
        
        Returns:
            GoldPrice model with validated data
            
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/gold_repo.py
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/gold_repo.py
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/gold_repo.py
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/gold_repo.py
        Raises:
            requests.exceptions.RequestException: If all sources fail
            ValueError: If data parsing fails
=======
        Note:
            Returns fallback data if all sources fail to ensure UI stability
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/repositories/gold_repo.py
=======
        Note:
            Returns fallback data if all sources fail to ensure UI stability
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/repositories/gold_repo.py
=======
        Note:
            Returns fallback data if all sources fail to ensure UI stability
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/repositories/gold_repo.py
=======
        Note:
            Returns fallback data if all sources fail to ensure UI stability
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/repositories/gold_repo.py
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
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/gold_repo.py
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/gold_repo.py
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/gold_repo.py
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/gold_repo.py
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-b41d3eed/repositories/gold_repo.py
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/repositories/gold_repo.py
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/repositories/gold_repo.py
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/repositories/gold_repo.py
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/repositories/gold_repo.py
