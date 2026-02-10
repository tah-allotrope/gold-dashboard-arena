"""
Historical data repository for Vietnam Gold Dashboard.
Fetches past prices from external APIs (CoinGecko, VPS, chogia.vn)
and falls back to the local history store for assets without APIs (SJC Gold).
"""

import time
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, Optional

import requests

from .base import Repository
from ..config import (
    CHOGIA_AJAX_URL,
    COINGECKO_MARKET_CHART_URL,
    HEADERS,
    HISTORY_PERIODS,
    REQUEST_TIMEOUT,
    VPS_VN30_API_URL,
)
from ..history_store import get_value_at, record_snapshot
from ..models import (
    AssetHistoricalData,
    DashboardData,
    HistoricalChange,
)

# CoinGecko free tier caps historical data at 365 days
_COINGECKO_MAX_DAYS = 365


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
    # Gold — chogia.vn SJC historical (~30 days) + local store fallback
    # ------------------------------------------------------------------

    def _gold_changes(self, current_value: Decimal) -> AssetHistoricalData:
        """
        Compute SJC gold price changes using actual SJC data from chogia.vn.

        chogia.vn returns ~30 days of real SJC sell prices, covering 1W and
        1M periods.  For 1Y and 3Y we fall back to the local history store
        which accumulates data over time as the scraper runs daily.

        As a bonus, each call backfills the local store with the 30 days of
        chogia.vn data so the store grows faster.
        """
        changes = []
        now = datetime.now()

        # Fetch ~30 days of real SJC prices from chogia.vn
        sjc_rates: Optional[Dict[str, Decimal]] = None
        try:
            sjc_rates = self._fetch_chogia_gold_history()
            # Backfill local store with the scraped data
            if sjc_rates:
                self._backfill_gold_history(sjc_rates)
        except (requests.exceptions.RequestException, ValueError, KeyError):
            pass

        for label, days in HISTORY_PERIODS.items():
            target_date = now - timedelta(days=days)
            old_value: Optional[Decimal] = None

            # Try chogia.vn data (covers ~30 days of actual SJC prices)
            if sjc_rates is not None:
                old_value = self._find_chogia_rate(sjc_rates, target_date)

            # Fall back to local history store for older periods
            if old_value is None:
                old_value = get_value_at("gold", target_date)

            change = HistoricalChange(period=label, new_value=current_value)
            if old_value is not None:
                change.old_value = old_value
                change.change_percent = _compute_change_percent(old_value, current_value)

            changes.append(change)

        return AssetHistoricalData(asset_name="gold", changes=changes)

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
    def _backfill_gold_history(rates: Dict[str, Decimal]) -> None:
        """
        Seed the local history store with chogia.vn SJC data.

        This ensures that even if we only get 30 days from the API,
        over months of running we accumulate a full year+ of real
        SJC prices in the local store.
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
