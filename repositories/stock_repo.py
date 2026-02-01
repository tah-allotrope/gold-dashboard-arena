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
