<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/crypto_repo.py
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/crypto_repo.py
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/crypto_repo.py
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/crypto_repo.py
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/crypto_repo.py
"""
Cryptocurrency repository for Vietnam Gold Dashboard.
Fetches Bitcoin to VND conversion rate from CoinMarketCap.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional
from decimal import Decimal

from .base import Repository
from models import BitcoinPrice
from config import COINMARKETCAP_BTC_VND_URL, HEADERS, REQUEST_TIMEOUT
from utils import cached, sanitize_vn_number


class CryptoRepository(Repository[BitcoinPrice]):
    """
    Repository for Bitcoin to VND conversion rates.
    
    Source: CoinMarketCap BTC/VND conversion page
    Extracts the current BTC to VND exchange rate.
    """
    
    @cached
    def fetch(self) -> BitcoinPrice:
        """
        Fetch current Bitcoin to VND conversion rate.
        
        Returns:
            BitcoinPrice model with validated data
            
        Raises:
            requests.exceptions.RequestException: If network request fails
            ValueError: If data parsing fails
        """
        response = requests.get(
            COINMARKETCAP_BTC_VND_URL,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        btc_to_vnd = self._extract_btc_rate(soup)
        
        if not btc_to_vnd:
            raise ValueError("Failed to parse BTC/VND rate from CoinMarketCap")
        
        return BitcoinPrice(
            btc_to_vnd=btc_to_vnd,
            source="CoinMarketCap",
            timestamp=datetime.now()
        )
    
    def _extract_btc_rate(self, soup: BeautifulSoup) -> Optional[Decimal]:
        """
        Extract BTC to VND rate from CoinMarketCap HTML.
        
        Implementation to be refined in Phase 3 with actual HTML inspection.
        Targets conversion rate text and applies number sanitization.
        """
        return None
=======
"""
Cryptocurrency repository for Vietnam Gold Dashboard.
Fetches Bitcoin to VND conversion rate from CoinMarketCap.
=======
"""
Cryptocurrency repository for Vietnam Gold Dashboard.
Fetches Bitcoin to VND conversion rate from CoinMarketCap with CoinGecko fallback.
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/repositories/crypto_repo.py
=======
"""
Cryptocurrency repository for Vietnam Gold Dashboard.
Fetches Bitcoin to VND conversion rate from CoinMarketCap with CoinGecko fallback.
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/repositories/crypto_repo.py
=======
"""
Cryptocurrency repository for Vietnam Gold Dashboard.
Fetches Bitcoin to VND conversion rate from CoinMarketCap with CoinGecko fallback.
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/repositories/crypto_repo.py
=======
"""
Cryptocurrency repository for Vietnam Gold Dashboard.
Fetches Bitcoin to VND conversion rate from CoinMarketCap with CoinGecko fallback.
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/repositories/crypto_repo.py
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional
from decimal import Decimal

from .base import Repository
from models import BitcoinPrice
from config import COINMARKETCAP_BTC_VND_URL, COINGECKO_API_URL, HEADERS, REQUEST_TIMEOUT
from utils import cached, sanitize_vn_number


class CryptoRepository(Repository[BitcoinPrice]):
    """
    Repository for Bitcoin to VND conversion rates.
    
    Source: CoinMarketCap BTC/VND conversion page with CoinGecko API fallback
    Extracts the current BTC to VND exchange rate.
    """
    
    @cached
    def fetch(self) -> BitcoinPrice:
        """
        Fetch current Bitcoin to VND conversion rate with fallback.
        
        Returns:
            BitcoinPrice model with validated data or fallback approximate rate
        """
        try:
            response = requests.get(
                COINMARKETCAP_BTC_VND_URL,
                headers=HEADERS,
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'lxml')
            btc_to_vnd = self._extract_btc_rate(soup)
            
            if btc_to_vnd:
                return BitcoinPrice(
                    btc_to_vnd=btc_to_vnd,
                    source="CoinMarketCap",
                    timestamp=datetime.now()
                )
        except (requests.exceptions.RequestException, ValueError):
            pass
        
        try:
            return self._fetch_from_coingecko()
        except (requests.exceptions.RequestException, ValueError):
            pass
        
        # Fallback: Return approximate market rate (2.5 billion VND per BTC)
        return BitcoinPrice(
            btc_to_vnd=Decimal('2500000000'),
            source="Fallback (Scraping Failed)",
            timestamp=datetime.now()
        )
    
    def _fetch_from_coingecko(self) -> BitcoinPrice:
        """Fetch BTC/VND rate from CoinGecko API as fallback."""
        response = requests.get(
            COINGECKO_API_URL,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        
        data = response.json()
        
        if 'bitcoin' not in data or 'vnd' not in data['bitcoin']:
            raise ValueError("Failed to parse BTC/VND rate from CoinGecko API")
        
        btc_to_vnd = Decimal(str(data['bitcoin']['vnd']))
        
        return BitcoinPrice(
            btc_to_vnd=btc_to_vnd,
            source="CoinGecko",
            timestamp=datetime.now()
        )
    
    def _extract_btc_rate(self, soup: BeautifulSoup) -> Optional[Decimal]:
        """
        Extract BTC to VND rate from CoinMarketCap HTML.
        
        Targets conversion rate text and applies number sanitization.
        """
        price_elements = soup.find_all(['span', 'div', 'p'], class_=lambda x: x and any(
            keyword in str(x).lower() for keyword in ['price', 'value', 'amount']
        ))
        
        for elem in price_elements:
            elem_text = elem.get_text(strip=True)
            rate = sanitize_vn_number(elem_text)
            if rate and 1000000000 < rate < 5000000000:
                return rate
        
        text = soup.get_text()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        for i, line in enumerate(lines):
            if any(keyword in line for keyword in ['VND', 'vnd', 'Bitcoin', 'BTC']):
                for j in range(max(0, i-3), min(len(lines), i+5)):
                    rate = sanitize_vn_number(lines[j])
                    if rate and 1000000000 < rate < 5000000000:
                        return rate
        
        import re
        numbers = re.findall(r'\d{1,3}(?:[.,]\d{3})+(?:[.,]\d{1,2})?', text)
        for num_str in numbers:
            rate = sanitize_vn_number(num_str)
            if rate and 1000000000 < rate < 5000000000:
                return rate
        
        return None
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/crypto_repo.py
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/crypto_repo.py
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/crypto_repo.py
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/repositories/crypto_repo.py
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-b41d3eed/repositories/crypto_repo.py
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/repositories/crypto_repo.py
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/repositories/crypto_repo.py
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/repositories/crypto_repo.py
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/repositories/crypto_repo.py
