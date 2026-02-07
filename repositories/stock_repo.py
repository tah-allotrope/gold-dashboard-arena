<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/stock_repo.py
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/stock_repo.py
"""
Stock index repository for Vietnam Gold Dashboard.
Fetches VN30 index data from Vietstock.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional, Tuple
from decimal import Decimal

from .base import Repository
from models import Vn30Index
from config import VIETSTOCK_URL, HEADERS, REQUEST_TIMEOUT
from utils import cached, sanitize_vn_number


class StockRepository(Repository[Vn30Index]):
    """
    Repository for VN30 stock index.
    
    Source: Vietstock VN30 index page
    Extracts current index value and percentage change.
    """
    
    @cached
    def fetch(self) -> Vn30Index:
        """
        Fetch current VN30 index value and change.
        
        Returns:
            Vn30Index model with validated data
            
        Raises:
            requests.exceptions.RequestException: If network request fails
            ValueError: If data parsing fails
        """
        response = requests.get(
            VIETSTOCK_URL,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        index_value, change_percent = self._extract_vn30_data(soup)
        
        if not index_value:
            raise ValueError("Failed to parse VN30 index from Vietstock")
        
        return Vn30Index(
            index_value=index_value,
            change_percent=change_percent,
            source="Vietstock",
            timestamp=datetime.now()
        )
    
    def _extract_vn30_data(self, soup: BeautifulSoup) -> Tuple[Optional[Decimal], Optional[Decimal]]:
        """
        Extract VN30 index value and percentage change from Vietstock HTML.
        
        The HTML contains text like: 'VN30-INDEX', '2,029.81', '10.83 (0.54%)'
        Line structure: line N has 'VN30-INDEX', line N+1 has value, line N+2 has change.
        
        Returns:
            Tuple of (index_value, change_percent) or (None, None)
        """
        text = soup.get_text()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        for i, line in enumerate(lines):
            if line == 'VN30-INDEX':
                if i + 1 < len(lines):
                    index_value = sanitize_vn_number(lines[i + 1])
                    
                    change_percent = None
                    if i + 2 < len(lines):
                        change_line = lines[i + 2]
                        if '(' in change_line and '%' in change_line:
                            import re
                            match = re.search(r'([-+]?\d+[.,]\d+)\s*\(', change_line)
                            if match:
                                change_percent = sanitize_vn_number(match.group(1))
                    
                    if index_value and index_value > 100 and index_value < 10000:
                        return (index_value, change_percent)
        
        return (None, None)
=======
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-b6dd527c/repositories/stock_repo.py
"""
Stock index repository for Vietnam Gold Dashboard.
Fetches VN30 index data from Vietstock.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional, Tuple
from decimal import Decimal

from .base import Repository
from models import Vn30Index
from config import VIETSTOCK_URL, CAFEF_URL, HEADERS, REQUEST_TIMEOUT, VPS_VN30_API_URL
from utils import cached, sanitize_vn_number


class StockRepository(Repository[Vn30Index]):
    """
    Repository for VN30 stock index.
    
    Source chain: Vietstock → VPS TradingView API → CafeF → Hardcoded fallback
    """
    
    @cached
    def fetch(self) -> Vn30Index:
        """
        Fetch current VN30 index value and change.
        
        Returns:
            Vn30Index model with validated data or fallback
        """
        # 1. Try Vietstock (Primary - Vietnamese scraping)
        try:
            return self._fetch_from_vietstock()
        except (requests.exceptions.RequestException, ValueError, KeyError) as e:
            print(f"Vietstock fetch failed: {e}")
        
        # 2. Try VPS TradingView API (works from international IPs)
        try:
            return self._fetch_from_vps_api()
        except (requests.exceptions.RequestException, ValueError, KeyError) as e:
            print(f"VPS API fetch failed: {e}")
        
        # 3. Try CafeF (Secondary scraping)
        try:
            return self._fetch_from_cafef()
        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"CafeF fetch failed: {e}")
        
        # 4. Hardcoded Fallback - ensures UI never shows "--"
        return Vn30Index(
            index_value=Decimal('1950.00'),
            change_percent=Decimal('0.0'),
            source="Fallback (Scraping Failed)",
            timestamp=datetime.now()
        )

    def _fetch_from_vietstock(self) -> Vn30Index:
        """Fetch from Vietstock."""
        response = requests.get(
            VIETSTOCK_URL,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        index_value, change_percent = self._extract_vn30_data(soup)
        
        if not index_value:
            raise ValueError("Failed to parse VN30 index from Vietstock")
        
        return Vn30Index(
            index_value=index_value,
            change_percent=change_percent,
            source="Vietstock",
            timestamp=datetime.now()
        )

    def _fetch_from_vps_api(self) -> Vn30Index:
        """
        Fetch VN30 index from VPS Securities TradingView-compatible API.
        
        This API works from international IPs (no geo-blocking).
        Returns OHLCV data; we use the latest close price and compute
        day-over-day change percent from the two most recent trading days.
        """
        import time
        now = int(time.time())
        week_ago = now - 7 * 86400
        
        url = f"{VPS_VN30_API_URL}&from={week_ago}&to={now}"
        response = requests.get(
            url,
            headers={"User-Agent": HEADERS["User-Agent"]},
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        
        data = response.json()
        
        if data.get('s') != 'ok' or not data.get('c'):
            raise ValueError("VPS API returned no VN30 data")
        
        closes = data['c']
        latest_close = Decimal(str(closes[-1]))
        
        change_percent = None
        if len(closes) >= 2:
            prev_close = Decimal(str(closes[-2]))
            if prev_close > 0:
                change_percent = ((latest_close - prev_close) / prev_close * 100).quantize(Decimal('0.01'))
        
        if latest_close < 100 or latest_close > 10000:
            raise ValueError(f"VN30 value {latest_close} outside expected range")
        
        return Vn30Index(
            index_value=latest_close,
            change_percent=change_percent,
            source="VPS",
            timestamp=datetime.now()
        )

    def _fetch_from_cafef(self) -> Vn30Index:
        """Fetch from CafeF."""
        response = requests.get(
            CAFEF_URL,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Look for the index value in typical CafeF structure
        # Usually in a div/span with class 'price', 'index', or similar
        # Or search for text near "VN30-INDEX"
        
        index_value = None
        change_percent = None
        
        text = soup.get_text()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        for i, line in enumerate(lines):
            # CafeF usually has the index name then the value nearby
            if 'VN30-INDEX' in line.upper():
                # Check next few lines for a number
                for j in range(i, min(len(lines), i + 10)):
                    val = sanitize_vn_number(lines[j])
                    if val and 100 < val < 10000:
                        index_value = val
                        # Try to find change percent nearby
                        if j + 1 < len(lines):
                            change = sanitize_vn_number(lines[j + 1])
                            if change is not None and -100 < change < 100:
                                change_percent = change
                        break
                if index_value:
                    break
        
        if not index_value:
             # Fallback: Try to find any large number that looks like an index
             # This is risky but better than nothing for a secondary fallback
            pass

        if not index_value:
            raise ValueError("Failed to parse VN30 index from CafeF")
            
        return Vn30Index(
            index_value=index_value,
            change_percent=change_percent,
            source="CafeF",
            timestamp=datetime.now()
        )
    
    def _extract_vn30_data(self, soup: BeautifulSoup) -> Tuple[Optional[Decimal], Optional[Decimal]]:
        """
        Extract VN30 index value and percentage change from Vietstock HTML.
        
        The HTML contains text like: 'VN30-INDEX', '2,029.81', '10.83 (0.54%)'
        Line structure: line N has 'VN30-INDEX', line N+1 has value, line N+2 has change.
        
        Returns:
            Tuple of (index_value, change_percent) or (None, None)
        """
        text = soup.get_text()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        for i, line in enumerate(lines):
            if line == 'VN30-INDEX':
                if i + 1 < len(lines):
                    index_value = sanitize_vn_number(lines[i + 1])
                    
                    change_percent = None
                    if i + 2 < len(lines):
                        change_line = lines[i + 2]
                        if '(' in change_line and '%' in change_line:
                            import re
                            match = re.search(r'([-+]?\d+[.,]\d+)\s*\(', change_line)
                            if match:
                                change_percent = sanitize_vn_number(match.group(1))
                    
                    if index_value and index_value > 100 and index_value < 10000:
                        return (index_value, change_percent)
        
        return (None, None)
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/stock_repo.py
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-8769c0a5/repositories/stock_repo.py
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-b6dd527c/repositories/stock_repo.py
