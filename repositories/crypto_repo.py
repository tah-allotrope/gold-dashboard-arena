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
from config import COINMARKETCAP_BTC_VND_URL, COINGECKO_API_URL, HEADERS, REQUEST_TIMEOUT
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
        # Try CoinMarketCap first
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
        
        # Fallback to CoinGecko API
        return self._fetch_from_coingecko()
    
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
        # Try to find price elements with common CoinMarketCap class patterns
        price_elements = soup.find_all(['span', 'div', 'p'], class_=lambda x: x and any(
            keyword in str(x).lower() for keyword in ['price', 'value', 'amount']
        ))
        
        for elem in price_elements:
            elem_text = elem.get_text(strip=True)
            # BTC/VND should be in billions (1-3 billion range typically)
            rate = sanitize_vn_number(elem_text)
            if rate and 1000000000 < rate < 10000000000:
                return rate
        
        # Try text-based extraction
        text = soup.get_text()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        for i, line in enumerate(lines):
            # Look for VND or Bitcoin-related indicators
            if any(keyword in line for keyword in ['VND', 'vnd', 'Bitcoin', 'BTC']):
                # Search nearby lines for large numbers
                for j in range(max(0, i-3), min(len(lines), i+5)):
                    rate = sanitize_vn_number(lines[j])
                    if rate and 1000000000 < rate < 10000000000:
                        return rate
        
        # Last resort: scan all text for numbers in the valid range
        import re
        numbers = re.findall(r'\d{1,3}(?:[.,]\d{3})+(?:[.,]\d{1,2})?', text)
        for num_str in numbers:
            rate = sanitize_vn_number(num_str)
            if rate and 1000000000 < rate < 10000000000:
                return rate
        
        return None
