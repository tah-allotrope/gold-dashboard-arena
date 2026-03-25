"""
Gasoline repository for fetching Vietnam retail gasoline prices.
"""

import json
import re
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import ClassVar, Dict, Optional, Tuple

import requests
from bs4 import BeautifulSoup

from .base import Repository
from ..config import (
    GASOLINE_FALLBACK_E5_RON92_PRICE,
    GASOLINE_MAX_AGE_DAYS,
    GASOLINE_FALLBACK_RON95_PRICE,
    GASOLINE_LAST_GOOD_SCRAPE_FILE,
    GASOLINE_MAX_VALID_VND,
    GASOLINE_MIN_VALID_VND,
    GASOLINE_UNIT,
    HEADERS,
    PETROLIMEX_URL,
    REQUEST_TIMEOUT,
    XANGDAU_URL,
)
from ..models import GasolinePrice
from ..utils import cached


class GasolineRepository(Repository[GasolinePrice]):
    """Fetches Vietnam retail gasoline prices with a 4-step fallback chain."""

    _GASOLINE_SEED: ClassVar[Dict[str, str]] = {
        "ron95_price": "25570",
        "e5_ron92_price": "22500",
        "source": "Manual gasoline seed",
        "unit": "VND/liter",
        "timestamp": "2026-03-01T00:00:00",
    }

    @staticmethod
    def is_seed_source(source: str) -> bool:
        """Return True when source represents embedded seed data."""
        return "seed" in source.lower()

    @staticmethod
    def is_fallback_source(source: str) -> bool:
        """Return True when source represents the hardcoded final fallback."""
        return source.lower().startswith("fallback")

    @staticmethod
    def is_cached_source(source: str) -> bool:
        """Return True when source comes from the last-good-scrape cache."""
        return "(cached)" in source.lower()

    @classmethod
    def is_realtime_source(cls, source: str) -> bool:
        """Return True only for direct live-source fetches."""
        return not (
            cls.is_seed_source(source)
            or cls.is_fallback_source(source)
            or cls.is_cached_source(source)
        )

    @staticmethod
    def is_stale_timestamp(timestamp: datetime, now: Optional[datetime] = None) -> bool:
        """Return True when gasoline data is older than the regulated repricing window."""
        effective_now = now or datetime.now()
        return timestamp < effective_now - timedelta(days=GASOLINE_MAX_AGE_DAYS)

    @classmethod
    def should_record_snapshot(
        cls, price: GasolinePrice, now: Optional[datetime] = None
    ) -> bool:
        """Persist only direct live gasoline observations that are still fresh."""
        return cls.is_realtime_source(price.source) and not cls.is_stale_timestamp(
            price.timestamp, now
        )

    @cached
    def fetch(self) -> GasolinePrice:
        """Fetch gasoline price with a 4-step fallback chain:
        1. xangdau.net scrape
        2. petrolimex.com.vn scrape
        3. Persisted last-good-scrape file
        4. Hardcoded fallback constants
        Returns the first successful result."""

        # Step 1: xangdau.net
        try:
            return self._fetch_from_xangdau()
        except Exception as e:
            print(f"  [Gasoline] xangdau.net failed: {e}")

        # Step 2: petrolimex.com.vn
        try:
            return self._fetch_from_petrolimex()
        except Exception as e:
            print(f"  [Gasoline] petrolimex.com.vn failed: {e}")

        # Step 3: Local persistence file
        try:
            cached_price = self._load_last_good_scrape()
            if cached_price:
                return cached_price
        except Exception as e:
            print(f"  [Gasoline] local cache failed: {e}")

        # Step 4: Hardcoded fallback
        print("  [Gasoline] All sources failed, using hardcoded fallback")
        return GasolinePrice(
            ron95_price=GASOLINE_FALLBACK_RON95_PRICE,
            e5_ron92_price=GASOLINE_FALLBACK_E5_RON92_PRICE,
            source="Fallback (Manual estimate)",
            unit=GASOLINE_UNIT,
        )

    def _fetch_from_xangdau(self) -> GasolinePrice:
        """GET xangdau.net, parse RON 95-III and E5 RON 92 prices from page text,
        validate against valid range, persist result, and return GasolinePrice.
        Raises ValueError if no valid RON 95-III price found.
        Raises requests.exceptions.RequestException on network failure."""
        response = requests.get(XANGDAU_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)

        ron95_price = self._extract_grade_price(text, "RON 95-III")
        if not ron95_price:
            raise ValueError("No valid RON 95-III price found on xangdau.net")

        e5_ron92_price = self._extract_grade_price(text, "E5 RON 92")

        price = GasolinePrice(
            ron95_price=ron95_price,
            e5_ron92_price=e5_ron92_price,
            source="xangdau.net",
            unit=GASOLINE_UNIT,
        )
        self._persist_last_good_scrape(price)
        return price

    def _fetch_from_petrolimex(self) -> GasolinePrice:
        """GET petrolimex.com.vn retail price page, parse table/text for RON 95
        and E5 RON 92 prices, validate, persist, and return GasolinePrice.
        Raises ValueError if no valid RON 95-III price found.
        Raises requests.exceptions.RequestException on network failure (geo-blocked outside VN)."""
        response = requests.get(
            PETROLIMEX_URL, headers=HEADERS, timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        text = soup.get_text(separator=" ", strip=True)

        # Look for RON 95-III. Sometimes they write it as RON 95-III, RON 95-V etc.
        # We will search for "RON 95" broadly or "RON 95-III" specifically.
        ron95_price = self._extract_grade_price(text, "RON 95-III")
        if not ron95_price:
            ron95_price = self._extract_grade_price(text, "RON 95")
            if not ron95_price:
                raise ValueError("No valid RON 95-III price found on petrolimex.com.vn")

        e5_ron92_price = self._extract_grade_price(text, "E5 RON 92")

        price = GasolinePrice(
            ron95_price=ron95_price,
            e5_ron92_price=e5_ron92_price,
            source="Petrolimex",
            unit=GASOLINE_UNIT,
        )
        self._persist_last_good_scrape(price)
        return price

    @staticmethod
    def _extract_grade_price(text: str, grade_label: str) -> Optional[Decimal]:
        """Search `text` for `grade_label` (case-insensitive), then scan up to 120
        chars after the label for a number pattern matching VND/liter range
        (GASOLINE_MIN_VALID_VND to GASOLINE_MAX_VALID_VND).
        Returns Decimal VND/liter if found, None otherwise.
        Handles both dot-thousands (22.500) and no-separator (22500) formats."""

        idx = text.lower().find(grade_label.lower())
        if idx == -1:
            return None

        search_area = text[idx : idx + 120]

        # Look for numbers that might look like 22.500, 22,500, or 22500
        # Regex to find numbers with optional single dot or comma as thousand separator
        matches = re.finditer(r"\b(\d{2})[.,]?(\d{3})\b", search_area)

        for match in matches:
            num_str = match.group(1) + match.group(2)
            try:
                val = Decimal(num_str)
                if GASOLINE_MIN_VALID_VND <= val <= GASOLINE_MAX_VALID_VND:
                    return val
            except InvalidOperation:
                continue

        return None

    @staticmethod
    def _persist_last_good_scrape(price: GasolinePrice) -> None:
        """Write successful scrape to GASOLINE_LAST_GOOD_SCRAPE_FILE as JSON.
        Best-effort — never raises; logs warning on failure.
        JSON keys: ron95_price, e5_ron92_price (may be null), source, unit, timestamp."""
        try:
            path = Path(GASOLINE_LAST_GOOD_SCRAPE_FILE)
            path.parent.mkdir(parents=True, exist_ok=True)

            data = {
                "ron95_price": str(price.ron95_price),
                "e5_ron92_price": str(price.e5_ron92_price)
                if price.e5_ron92_price
                else None,
                "source": price.source,
                "unit": price.unit,
                "timestamp": price.timestamp.isoformat(),
            }

            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f)
        except Exception as e:
            print(f"  [Gasoline] Warning: Failed to persist scrape: {e}")

    @classmethod
    def _load_last_good_scrape(cls) -> Optional[GasolinePrice]:
        """Load GasolinePrice from GASOLINE_LAST_GOOD_SCRAPE_FILE if it exists and is valid.
        Falls back to cls._GASOLINE_SEED if file does not exist.
        Returns None if stored price is outside valid range.
        Source string gets ' (cached)' or ' (seed)' suffix appended."""
        path = Path(GASOLINE_LAST_GOOD_SCRAPE_FILE)
        data = None
        is_seed = False

        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                pass

        if not data:
            data = cls._GASOLINE_SEED
            is_seed = True

        try:
            ron95_val = Decimal(str(data.get("ron95_price", "0")))
            if not (GASOLINE_MIN_VALID_VND <= ron95_val <= GASOLINE_MAX_VALID_VND):
                return None

            e5_str = data.get("e5_ron92_price")
            e5_val = Decimal(str(e5_str)) if e5_str else None

            source_base = data.get("source", "Unknown")
            suffix = " (seed)" if is_seed else " (cached)"
            # ensure we don't append multiple times if already there
            if not source_base.endswith(suffix):
                source = f"{source_base}{suffix}"
            else:
                source = source_base

            timestamp_str = data.get("timestamp")
            if timestamp_str:
                dt = datetime.fromisoformat(timestamp_str)
            else:
                dt = datetime.now()

            return GasolinePrice(
                ron95_price=ron95_val,
                e5_ron92_price=e5_val,
                source=source,
                unit=data.get("unit", GASOLINE_UNIT),
                timestamp=dt,
            )
        except Exception:
            return None
