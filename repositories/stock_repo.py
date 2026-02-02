"""
Stock index repository for Vietnam Gold Dashboard.
Fetches VN30 index data from Vietstock.
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional, Tuple
from decimal import Decimal
import re

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
        
        Returns:
            Tuple of (index_value, change_percent) or (None, None)
        """
        text = soup.get_text()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        for i, line in enumerate(lines):
            if 'VN30-INDEX' in line:
                # Search in nearby lines
                for j in range(i, min(len(lines), i + 5)):
                    val = sanitize_vn_number(lines[j])
                    if val and 500 < val < 5000:
                        index_value = val

                        # Look for change percentage in subsequent lines
                        change_percent = None
                        for k in range(j + 1, min(len(lines), j + 5)):
                            if '%' in lines[k]:
                                match = re.search(r'\(([-+]?\d+[.,]\d+)%\)', lines[k])
                                if match:
                                    change_percent = sanitize_vn_number(match.group(1))
                                    break
                                # Alternative: just any number followed by %
                                match = re.search(r'([-+]?\d+[.,]\d+)%', lines[k])
                                if match:
                                    change_percent = sanitize_vn_number(match.group(1))
                                    break

                        return (index_value, change_percent)
        
        return (None, None)
