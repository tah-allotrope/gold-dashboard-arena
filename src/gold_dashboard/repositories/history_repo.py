"""
Historical data repository for Vietnam Gold Dashboard.
Fetches past prices from external APIs (CoinGecko, VPS, chogia.vn)
and falls back to the local history store for assets without APIs (SJC Gold).
"""

import json
import re
import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

import requests

from .base import Repository
from ..config import (
    CHOGIA_AJAX_URL,
    COINGECKO_MARKET_CHART_URL,
    HEADERS,
    HISTORY_PERIODS,
    REQUEST_TIMEOUT,
    VPS_VN30_API_URL,
    WEBGIA_GOLD_1Y_URL,
)
from ..history_store import get_value_at, record_snapshot
from ..models import (
    AssetHistoricalData,
    DashboardData,
    HistoricalChange,
)

# CoinGecko free tier caps historical data at 365 days
_COINGECKO_MAX_DAYS = 365

# Regex to extract the "Bán ra" (sell) series from webgia.com inline JS.
# The page embeds Highcharts data like: {name:"Bán ra", data:[[ts,price],...]}
_WEBGIA_SELL_RE = re.compile(r'name:.B.n ra.,\s*data:(\[\[.*?\]\])')

# Verified historical SJC sell prices (VND/tael) from Vietnamese news archives.
# These seed the local history store so 3Y data is available immediately.
# Sources: VnExpress, Tuoi Tre, CafeF — prices are for SJC 1-lượng sell in HCMC.
_SJC_HISTORICAL_SEEDS: List[Tuple[str, Decimal]] = [
    ("2023-02-10", Decimal("66800000")),   # ~66.8M — VnExpress Feb 2023
    ("2023-06-01", Decimal("67500000")),   # ~67.5M — stable mid-2023
    ("2023-10-01", Decimal("69000000")),   # ~69.0M — Q4 2023
    ("2024-02-10", Decimal("79000000")),   # ~79.0M — VnExpress Feb 2024
    ("2024-06-01", Decimal("87500000")),   # ~87.5M — post-rally mid-2024
    ("2024-10-01", Decimal("84000000")),   # ~84.0M — VnExpress Oct 2024
    ("2025-01-01", Decimal("85000000")),   # ~85.0M — start of 2025
]


def _compute_change_percent(old_value: Decimal, new_value: Decimal) -> Decimal:
    """Compute percentage change from old to new, rounded to 2 decimal places."""
    if old_value == 0:
        return Decimal("0")
    return ((new_value - old_value) / old_value * 100).quantize(Decimal("0.01"))


class HistoryRepository:
    """
    Aggregates historical price data for all dashboard assets.

    For each asset it tries an external API first, then falls back to the
    local history store.  Every sub-fetch is wrapped in try/except so a
    single failure never blocks the rest.
    """

    def fetch_changes(self, current_data: DashboardData) -> Dict[str, AssetHistoricalData]:
        """
        Build a dict mapping asset keys to their historical change data.

        Args:
            current_data: The latest DashboardData with current prices.

        Returns:
            Dict like {"gold": AssetHistoricalData(...), "bitcoin": ...}
        """
        result: Dict[str, AssetHistoricalData] = {}

        if current_data.gold:
            result["gold"] = self._gold_changes(current_data.gold.sell_price)

        if current_data.usd_vnd:
            result["usd_vnd"] = self._usd_vnd_changes(current_data.usd_vnd.sell_rate)

        if current_data.bitcoin:
            result["bitcoin"] = self._bitcoin_changes(current_data.bitcoin.btc_to_vnd)

        if current_data.vn30:
            result["vn30"] = self._vn30_changes(current_data.vn30.index_value)

        return result

    # ------------------------------------------------------------------
    # Gold — webgia.com (~1 year) + chogia.vn (~30 days) + local store
    # ------------------------------------------------------------------

    def _gold_changes(self, current_value: Decimal) -> AssetHistoricalData:
        """
        Compute SJC gold price changes using a tiered strategy:

        1. **webgia.com** — embeds ~282 days of real SJC sell prices in
           inline Highcharts JS.  Covers 1W, 1M, and 1Y.
        2. **chogia.vn** — AJAX endpoint with ~30 days of SJC prices.
           Used as fallback for recent data if webgia is down.
        3. **Local history store** — seeded with verified news prices
           for 3Y, and backfilled with scraped data on every run.
        """
        changes = []
        now = datetime.now()

        # Ensure verified historical seeds are in the local store (for 3Y)
        self._seed_historical_gold()

        # Primary: webgia.com 1-year chart (~282 data points)
        webgia_rates: Optional[Dict[str, Decimal]] = None
        try:
            webgia_rates = self._fetch_webgia_gold_history()
            if webgia_rates:
                self._backfill_gold_history(webgia_rates)
        except (requests.exceptions.RequestException, ValueError, KeyError):
            pass

        # Fallback: chogia.vn ~30 days (finer granularity for recent data)
        chogia_rates: Optional[Dict[str, Decimal]] = None
        if webgia_rates is None:
            try:
                chogia_rates = self._fetch_chogia_gold_history()
                if chogia_rates:
                    self._backfill_gold_history(chogia_rates)
            except (requests.exceptions.RequestException, ValueError, KeyError):
                pass

        for label, days in HISTORY_PERIODS.items():
            target_date = now - timedelta(days=days)
            old_value: Optional[Decimal] = None

            # Try webgia.com data first (covers ~1 year)
            if webgia_rates is not None:
                old_value = self._find_chogia_rate(webgia_rates, target_date)

            # Try chogia.vn data (covers ~30 days)
            if old_value is None and chogia_rates is not None:
                old_value = self._find_chogia_rate(chogia_rates, target_date)

            # Fall back to local history store (has 3Y seeds + backfilled data)
            if old_value is None:
                old_value = get_value_at("gold", target_date)

            change = HistoricalChange(period=label, new_value=current_value)
            if old_value is not None:
                change.old_value = old_value
                change.change_percent = _compute_change_percent(old_value, current_value)

            changes.append(change)

        return AssetHistoricalData(asset_name="gold", changes=changes)

    def _fetch_webgia_gold_history(self) -> Dict[str, Decimal]:
        """
        GET webgia.com 1-year SJC chart page and extract inline Highcharts data.

        The page embeds a JS variable like:
            var seriesOptions = [{name:"Bán ra", data:[[ts_ms, price], ...]}]

        Prices are in millions VND (e.g. 90.3 = 90,300,000 VND).
        Returns a dict mapping YYYY-MM-DD -> Decimal full VND price.
        """
        response = requests.get(
            WEBGIA_GOLD_1Y_URL,
            headers=HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()

        match = _WEBGIA_SELL_RE.search(response.text)
        if not match:
            raise ValueError("Could not find sell series in webgia.com HTML")

        raw_data: List[List[float]] = json.loads(match.group(1))

        rates: Dict[str, Decimal] = {}
        for ts_ms, price_millions in raw_data:
            try:
                dt = datetime.fromtimestamp(ts_ms / 1000)
                date_key = dt.strftime("%Y-%m-%d")
                # Convert millions to full VND (e.g. 90.3 -> 90,300,000)
                rates[date_key] = Decimal(str(price_millions)) * 1_000_000
            except (ValueError, OSError):
                continue

        return rates

    def _fetch_chogia_gold_history(self) -> Dict[str, Decimal]:
        """
        POST chogia.vn AJAX endpoint for SJC gold historical prices.

        Returns a dict mapping date strings (YYYY-MM-DD) to sell prices
        in VND (full value, e.g. 181030000).

        The API returns dates as DD/MM (no year), so we infer the year
        from the current date.  Prices are in thousands (e.g. 181030 =
        181,030,000 VND).
        """
        response = requests.post(
            CHOGIA_AJAX_URL,
            headers={
                **HEADERS,
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "action": "load_gia_vang_cho_do_thi",
                "congty": "SJC",
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        if not data.get("success") or not data.get("data"):
            raise ValueError("chogia.vn returned unsuccessful gold response")

        now = datetime.now()
        rates: Dict[str, Decimal] = {}

        for entry in data["data"]:
            raw_date = entry.get("ngay", "")       # e.g. "12/01"
            sell_str = entry.get("gia_ban", "")     # e.g. "181030"
            if not raw_date or not sell_str:
                continue

            # Parse DD/MM and infer year
            try:
                day, month = raw_date.split("/")
                day_int, month_int = int(day), int(month)
                # If the month is ahead of the current month, it belongs
                # to the previous year (e.g. data from Dec seen in Jan)
                year = now.year if month_int <= now.month else now.year - 1
                date_key = f"{year}-{month_int:02d}-{day_int:02d}"
            except (ValueError, IndexError):
                continue

            # Prices are in thousands VND (e.g. 181030 -> 181,030,000)
            try:
                rates[date_key] = Decimal(sell_str) * 1000
            except Exception:
                continue

        return rates

    @staticmethod
    def _seed_historical_gold() -> None:
        """
        Plant verified SJC prices from news archives into the local store.

        This runs on every call but ``record_snapshot`` deduplicates by date,
        so repeated calls are cheap no-ops after the first seed.
        """
        for date_str, value in _SJC_HISTORICAL_SEEDS:
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                record_snapshot("gold", value, dt)
            except (ValueError, TypeError):
                continue

    @staticmethod
    def _backfill_gold_history(rates: Dict[str, Decimal]) -> None:
        """
        Seed the local history store with scraped SJC data.

        This ensures that over time the store accumulates a full multi-year
        record of real SJC prices from webgia.com and chogia.vn.
        """
        for date_str, value in rates.items():
            try:
                dt = datetime.strptime(date_str, "%Y-%m-%d")
                record_snapshot("gold", value, dt)
            except (ValueError, TypeError):
                continue

    # ------------------------------------------------------------------
    # USD/VND — chogia.vn (30 days of history) + local store fallback
    # ------------------------------------------------------------------

    def _usd_vnd_changes(self, current_value: Decimal) -> AssetHistoricalData:
        """Fetch historical USD/VND rates from chogia.vn, fall back to local store."""
        changes = []
        now = datetime.now()

        # chogia.vn returns ~30 days of daily rates; fetch once and reuse
        chogia_rates: Optional[Dict[str, Decimal]] = None
        try:
            chogia_rates = self._fetch_chogia_history()
        except (requests.exceptions.RequestException, ValueError, KeyError):
            pass

        for label, days in HISTORY_PERIODS.items():
            target_date = now - timedelta(days=days)
            old_value: Optional[Decimal] = None

            # Try chogia.vn data (covers ~30 days)
            if chogia_rates is not None:
                old_value = self._find_chogia_rate(chogia_rates, target_date)

            # Fall back to local history store
            if old_value is None:
                old_value = get_value_at("usd_vnd", target_date)

            change = HistoricalChange(period=label, new_value=current_value)
            if old_value is not None:
                change.old_value = old_value
                change.change_percent = _compute_change_percent(old_value, current_value)

            changes.append(change)

        return AssetHistoricalData(asset_name="usd_vnd", changes=changes)

    def _fetch_chogia_history(self) -> Dict[str, Decimal]:
        """
        POST chogia.vn AJAX endpoint for USD historical rates.
        Returns a dict mapping date strings (YYYY-MM-DD) to sell rates.
        """
        response = requests.post(
            CHOGIA_AJAX_URL,
            headers={
                **HEADERS,
                "Content-Type": "application/x-www-form-urlencoded",
            },
            data={
                "action": "load_gia_ngoai_te_cho_do_thi",
                "ma": "USD",
            },
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        if not data.get("success") or not data.get("data"):
            raise ValueError("chogia.vn returned unsuccessful response")

        rates: Dict[str, Decimal] = {}
        for entry in data["data"]:
            date_str = entry.get("ngay", "")
            sell_str = entry.get("gia_ban", "")
            if date_str and sell_str:
                rates[date_str] = Decimal(sell_str)

        return rates

    @staticmethod
    def _find_chogia_rate(rates: Dict[str, Decimal], target: datetime) -> Optional[Decimal]:
        """Find the chogia.vn rate closest to *target* within ±3 days."""
        for offset in range(4):
            for sign in (0, 1, -1):
                check_date = target + timedelta(days=sign * offset)
                key = check_date.strftime("%Y-%m-%d")
                if key in rates:
                    return rates[key]
        return None

    # ------------------------------------------------------------------
    # Bitcoin — CoinGecko market_chart API (free tier: max 365 days)
    # ------------------------------------------------------------------

    def _bitcoin_changes(self, current_value: Decimal) -> AssetHistoricalData:
        """
        Fetch historical BTC/VND prices from CoinGecko per period.

        CoinGecko free tier caps at 365 days, so periods beyond that
        (e.g. 3Y) fall back to the local history store.
        """
        changes = []
        now = datetime.now()

        # Fetch the largest *supported* window once and reuse for all periods
        fetch_days = min(max(HISTORY_PERIODS.values()), _COINGECKO_MAX_DAYS)
        price_history: Optional[Dict[int, Decimal]] = None

        try:
            price_history = self._fetch_coingecko_history(fetch_days)
        except (requests.exceptions.RequestException, ValueError, KeyError):
            pass

        for label, days in HISTORY_PERIODS.items():
            target_date = now - timedelta(days=days)
            old_value: Optional[Decimal] = None

            # Only use CoinGecko data if the period is within the free-tier cap
            if price_history is not None and days <= _COINGECKO_MAX_DAYS:
                old_value = self._find_closest_price(price_history, target_date)

            # Fall back to local history store
            if old_value is None:
                old_value = get_value_at("bitcoin", target_date)

            change = HistoricalChange(period=label, new_value=current_value)
            if old_value is not None:
                change.old_value = old_value
                change.change_percent = _compute_change_percent(old_value, current_value)

            changes.append(change)

        return AssetHistoricalData(asset_name="bitcoin", changes=changes)

    def _fetch_coingecko_history(self, days: int) -> Dict[int, Decimal]:
        """
        GET .../market_chart?vs_currency=vnd&days=N
        Returns {"prices": [[timestamp_ms, price], ...], ...}
        We build a dict mapping unix-day -> Decimal price.
        """
        url = f"{COINGECKO_MARKET_CHART_URL}&days={days}"
        response = requests.get(
            url,
            headers={"User-Agent": HEADERS["User-Agent"]},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        prices = data.get("prices", [])
        day_prices: Dict[int, Decimal] = {}
        for ts_ms, price in prices:
            day_key = int(ts_ms / 1000 / 86400)
            day_prices[day_key] = Decimal(str(price))

        return day_prices

    @staticmethod
    def _find_closest_price(day_prices: Dict[int, Decimal], target: datetime) -> Optional[Decimal]:
        """Find the price entry closest to *target* within ±3 days."""
        target_day = int(target.timestamp() / 86400)
        for offset in range(4):
            if target_day + offset in day_prices:
                return day_prices[target_day + offset]
            if target_day - offset in day_prices:
                return day_prices[target_day - offset]
        return None

    # ------------------------------------------------------------------
    # VN30 — VPS TradingView API (already used in stock_repo.py)
    # ------------------------------------------------------------------

    def _vn30_changes(self, current_value: Decimal) -> AssetHistoricalData:
        """Fetch historical VN30 closes from VPS API, fall back to local store."""
        changes = []
        now = datetime.now()

        # Fetch the longest period once
        max_days = max(HISTORY_PERIODS.values())
        close_history: Optional[Dict[int, Decimal]] = None

        try:
            close_history = self._fetch_vps_history(max_days)
        except (requests.exceptions.RequestException, ValueError, KeyError):
            pass

        for label, days in HISTORY_PERIODS.items():
            target_date = now - timedelta(days=days)
            old_value: Optional[Decimal] = None

            if close_history is not None:
                old_value = self._find_closest_price(close_history, target_date)

            if old_value is None:
                old_value = get_value_at("vn30", target_date)

            change = HistoricalChange(period=label, new_value=current_value)
            if old_value is not None:
                change.old_value = old_value
                change.change_percent = _compute_change_percent(old_value, current_value)

            changes.append(change)

        return AssetHistoricalData(asset_name="vn30", changes=changes)

    def _fetch_vps_history(self, days: int) -> Dict[int, Decimal]:
        """
        GET histdatafeed.vps.com.vn/tradingview/history?symbol=VN30&resolution=D&from=...&to=...
        Returns {"s":"ok","t":[timestamps],"c":[closes],...}
        We build a dict mapping unix-day -> Decimal close.
        """
        now_ts = int(time.time())
        from_ts = now_ts - days * 86400
        url = f"{VPS_VN30_API_URL}&from={from_ts}&to={now_ts}"

        response = requests.get(
            url,
            headers={"User-Agent": HEADERS["User-Agent"]},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()

        if data.get("s") != "ok" or not data.get("c") or not data.get("t"):
            raise ValueError("VPS API returned no VN30 historical data")

        timestamps = data["t"]
        closes = data["c"]
        day_prices: Dict[int, Decimal] = {}

        for ts, close in zip(timestamps, closes):
            day_key = int(ts / 86400)
            day_prices[day_key] = Decimal(str(close))

        return day_prices
