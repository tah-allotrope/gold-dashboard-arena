"""Land price repository for Vietnam Gold Dashboard."""

import re
from datetime import datetime
from decimal import Decimal
from statistics import median
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

from .base import Repository
from ..config import (
    ALONHADAT_Q11_URL,
    HEADERS,
    LAND_FALLBACK_PRICE_PER_M2,
    LAND_LOCATION,
    LAND_MAX_VALID_VND_PER_M2,
    LAND_MIN_VALID_VND_PER_M2,
    LAND_UNIT,
    REQUEST_TIMEOUT,
)
from ..models import LandPrice
from ..utils import cached


class LandRepository(Repository[LandPrice]):
    """Repository for land price per m2 around Hong Bang street, District 11."""

    @cached
    def fetch(self) -> LandPrice:
        """Fetch land price from alonhadat and fall back to configured default."""
        try:
            return self._fetch_from_alonhadat()
        except (requests.exceptions.RequestException, ValueError) as e:
            print(f"alonhadat fetch failed: {e}")

        return LandPrice(
            price_per_m2=LAND_FALLBACK_PRICE_PER_M2,
            source="Fallback (Manual estimate)",
            location=LAND_LOCATION,
            unit=LAND_UNIT,
            timestamp=datetime.now(),
        )

    def _fetch_from_alonhadat(self) -> LandPrice:
        """Extract listing-derived VND/m2 values from Quận 11 page and return a robust median."""
        response = requests.get(
            ALONHADAT_Q11_URL,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        unit_prices = self._extract_hong_bang_unit_prices(response.text)
        valid_prices = [
            p for p in unit_prices
            if LAND_MIN_VALID_VND_PER_M2 <= p <= LAND_MAX_VALID_VND_PER_M2
        ]

        if not valid_prices:
            raise ValueError("No valid Hong Bang listing prices parsed from alonhadat")

        return LandPrice(
            price_per_m2=median(valid_prices),
            source="alonhadat.com.vn",
            location=LAND_LOCATION,
            unit=LAND_UNIT,
            timestamp=datetime.now(),
        )

    def _extract_hong_bang_unit_prices(self, html: str) -> List[Decimal]:
        """Parse snippets around Hong Bang mentions and compute VND/m2 from (price, area)."""
        text = BeautifulSoup(html, "lxml").get_text(" ", strip=True)
        prices: List[Decimal] = []

        for match in re.finditer(r"h[oồ]ng\s*b[aà]ng", text, flags=re.IGNORECASE):
            start = max(0, match.start() - 25)
            end = min(len(text), match.end() + 180)
            snippet = text[start:end]

            area = self._extract_area_m2(snippet)
            price_billion = self._extract_price_billion(snippet)
            if area is None or area <= 0 or price_billion is None:
                continue

            price_vnd = price_billion * Decimal("1000000000")
            prices.append((price_vnd / area).quantize(Decimal("0.01")))

        return prices

    @staticmethod
    def _extract_area_m2(snippet: str) -> Optional[Decimal]:
        """Parse dimensions like 4x12 or 12 x 20m and return area in m2."""
        dim_match = re.search(r"(\d+(?:[.,]\d+)?)\s*[xX]\s*(\d+(?:[.,]\d+)?)", snippet)
        if dim_match:
            width = Decimal(dim_match.group(1).replace(",", "."))
            length = Decimal(dim_match.group(2).replace(",", "."))
            return width * length

        area_match = re.search(r"(\d+(?:[.,]\d+)?)\s*m\s*²", snippet, flags=re.IGNORECASE)
        if area_match:
            return Decimal(area_match.group(1).replace(",", "."))

        return None

    @staticmethod
    def _extract_price_billion(snippet: str) -> Optional[Decimal]:
        """Parse prices like 12 tỷ 5, 9 tỷ 98, or 45 tỷ into billion-VND units."""
        price_match = re.search(
            r"(\d+(?:[.,]\d+)?)\s*t(?:ỷ|y)(?:\s*(\d{1,3}))?",
            snippet,
            flags=re.IGNORECASE,
        )
        if not price_match:
            return None

        major = Decimal(price_match.group(1).replace(",", "."))
        minor_part = price_match.group(2)
        if not minor_part:
            return major

        minor = Decimal(minor_part)
        scale = Decimal("10") ** len(minor_part)
        return major + (minor / scale)
