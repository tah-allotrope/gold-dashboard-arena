"""
Tests for history_store and HistoryRepository.
Uses unittest with mocking to avoid real network calls.
"""

import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, MagicMock

from gold_dashboard.config import HISTORY_PERIODS
from gold_dashboard.history_store import (
    record_snapshot,
    get_value_at,
    get_all_entries,
    _load_history,
    _save_history,
    HISTORY_FILE,
)
from gold_dashboard.models import (
    AssetHistoricalData,
    BitcoinPrice,
    DashboardData,
    GoldPrice,
    HistoricalChange,
    UsdVndRate,
    Vn30Index,
)
from gold_dashboard.repositories.history_repo import (
    HistoryRepository,
    _compute_change_percent,
    _USD_VND_HISTORICAL_SEEDS,
    _BTC_VND_HISTORICAL_SEEDS,
)


class TestComputeChangePercent(unittest.TestCase):
    """Test the percentage change helper."""

    def test_positive_change(self) -> None:
        result = _compute_change_percent(Decimal("100"), Decimal("120"))
        self.assertEqual(result, Decimal("20.00"))

    def test_negative_change(self) -> None:
        result = _compute_change_percent(Decimal("100"), Decimal("80"))
        self.assertEqual(result, Decimal("-20.00"))

    def test_no_change(self) -> None:
        result = _compute_change_percent(Decimal("100"), Decimal("100"))
        self.assertEqual(result, Decimal("0.00"))

    def test_zero_old_value(self) -> None:
        result = _compute_change_percent(Decimal("0"), Decimal("100"))
        self.assertEqual(result, Decimal("0"))


class TestHistoryStore(unittest.TestCase):
    """Test the local JSON history store (uses a temp file)."""

    def setUp(self) -> None:
        self._tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        )
        self._tmp.close()
        self._patch = patch(
            "gold_dashboard.history_store.HISTORY_FILE", self._tmp.name
        )
        self._patch.start()

    def tearDown(self) -> None:
        self._patch.stop()
        if os.path.exists(self._tmp.name):
            os.unlink(self._tmp.name)

    def test_record_and_retrieve(self) -> None:
        """Record a snapshot and retrieve it for the same day."""
        ts = datetime(2025, 6, 1, 12, 0, 0)
        record_snapshot("gold", Decimal("175000000"), timestamp=ts)

        value = get_value_at("gold", ts)
        self.assertEqual(value, Decimal("175000000"))

    def test_deduplication_same_day(self) -> None:
        """Recording twice on the same day should update, not duplicate."""
        ts1 = datetime(2025, 6, 1, 10, 0, 0)
        ts2 = datetime(2025, 6, 1, 14, 0, 0)
        record_snapshot("gold", Decimal("100"), timestamp=ts1)
        record_snapshot("gold", Decimal("200"), timestamp=ts2)

        entries = get_all_entries("gold")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["value"], "200")

    def test_multiple_days(self) -> None:
        """Entries for different days should all be stored."""
        for day in range(1, 4):
            ts = datetime(2025, 6, day, 12, 0, 0)
            record_snapshot("gold", Decimal(str(day * 100)), timestamp=ts)

        entries = get_all_entries("gold")
        self.assertEqual(len(entries), 3)

    def test_get_value_at_closest(self) -> None:
        """Should return the closest snapshot within tolerance."""
        record_snapshot("gold", Decimal("100"), datetime(2025, 6, 1))
        record_snapshot("gold", Decimal("200"), datetime(2025, 6, 10))

        # Ask for June 2 — should get June 1 value (1 day away)
        value = get_value_at("gold", datetime(2025, 6, 2))
        self.assertEqual(value, Decimal("100"))

    def test_get_value_at_too_far(self) -> None:
        """Should return None if closest snapshot is beyond tolerance."""
        record_snapshot("gold", Decimal("100"), datetime(2025, 1, 1))

        # Ask for June 1 — way too far from Jan 1
        value = get_value_at("gold", datetime(2025, 6, 1))
        self.assertIsNone(value)

    def test_get_value_at_uses_calendar_day_tolerance(self) -> None:
        """A snapshot exactly 3 calendar days away should still match despite time-of-day offset."""
        record_snapshot("gold", Decimal("66800000"), datetime(2023, 2, 10, 0, 0, 0))

        # Mirrors the CI drift scenario where target time is later in the day.
        value = get_value_at("gold", datetime(2023, 2, 13, 19, 33, 0))
        self.assertEqual(value, Decimal("66800000"))

    def test_get_value_at_empty(self) -> None:
        """Should return None for an asset with no history."""
        value = get_value_at("gold", datetime(2025, 6, 1))
        self.assertIsNone(value)

    def test_multiple_assets(self) -> None:
        """Different assets should be stored independently."""
        ts = datetime(2025, 6, 1)
        record_snapshot("gold", Decimal("100"), ts)
        record_snapshot("bitcoin", Decimal("999"), ts)

        self.assertEqual(get_value_at("gold", ts), Decimal("100"))
        self.assertEqual(get_value_at("bitcoin", ts), Decimal("999"))


class TestHistoryRepository(unittest.TestCase):
    """Test HistoryRepository with mocked external API calls."""

    def _make_dashboard_data(self) -> DashboardData:
        return DashboardData(
            gold=GoldPrice(
                buy_price=Decimal("175000000"),
                sell_price=Decimal("176000000"),
                source="Test",
            ),
            usd_vnd=UsdVndRate(sell_rate=Decimal("25800"), source="Test"),
            bitcoin=BitcoinPrice(btc_to_vnd=Decimal("2600000000"), source="Test"),
            vn30=Vn30Index(index_value=Decimal("1300"), source="Test"),
        )

    @patch("gold_dashboard.repositories.history_repo.record_snapshot")
    @patch("gold_dashboard.repositories.history_repo.get_value_at")
    @patch("gold_dashboard.repositories.history_repo.requests.post")
    @patch("gold_dashboard.repositories.history_repo.requests.get")
    def test_fetch_changes_returns_all_assets(
        self, mock_get: MagicMock, mock_post: MagicMock, mock_local: MagicMock,
        mock_record: MagicMock,
    ) -> None:
        """fetch_changes should return a dict with all 4 asset keys."""
        # Make all external calls fail so we fall through to local store
        import requests.exceptions
        mock_get.side_effect = requests.exceptions.ConnectionError("network down")
        mock_post.side_effect = requests.exceptions.ConnectionError("network down")
        mock_local.return_value = None

        repo = HistoryRepository()
        data = self._make_dashboard_data()
        result = repo.fetch_changes(data)

        self.assertIn("gold", result)
        self.assertIn("usd_vnd", result)
        self.assertIn("bitcoin", result)
        self.assertIn("vn30", result)

        # Each asset should have all configured periods (including 1D)
        for key in ["gold", "usd_vnd", "bitcoin", "vn30"]:
            self.assertEqual(len(result[key].changes), len(HISTORY_PERIODS))
            self.assertEqual(
                [c.period for c in result[key].changes],
                list(HISTORY_PERIODS.keys()),
            )

    @patch("gold_dashboard.repositories.history_repo.record_snapshot")
    @patch("gold_dashboard.repositories.history_repo.get_value_at")
    @patch("gold_dashboard.repositories.history_repo.requests.get")
    def test_gold_webgia_success(
        self, mock_get: MagicMock, mock_local: MagicMock, mock_record: MagicMock
    ) -> None:
        """When webgia.com returns 1Y of SJC data, gold 1W/1M/1Y should be computed."""
        import json as _json
        now = datetime.now()

        # Build fake webgia.com inline Highcharts data spanning ~1 year.
        # Real data has ~282 points over 365 days (not every day has a price).
        # We generate 366 points to ensure the 1Y target (365 days ago) is covered.
        data_points = []
        for days_ago in range(366):
            dt = now - timedelta(days=365 - days_ago)
            ts_ms = dt.timestamp() * 1000
            price_millions = 90.0 + days_ago * 0.25  # gradual rise
            data_points.append([ts_ms, round(price_millions, 1)])

        inline_js = (
            'var seriesOptions = [{name:"Bán ra",'
            f'data:{_json.dumps(data_points)}'
            '}]'
        )
        fake_html = f'<html><script>{inline_js}</script></html>'

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.text = fake_html
        mock_get.return_value = mock_response
        mock_local.return_value = None

        repo = HistoryRepository()
        result = repo._gold_changes(Decimal("181000000"))

        self.assertEqual(result.asset_name, "gold")
        self.assertEqual(len(result.changes), len(HISTORY_PERIODS))

        change_map = {c.period: c for c in result.changes}
        self.assertIsNotNone(change_map["1D"].change_percent, "1D should have data")
        self.assertIsNotNone(change_map["1W"].change_percent, "1W should have data")
        self.assertIsNotNone(change_map["1M"].change_percent, "1M should have data")
        self.assertIsNotNone(change_map["1Y"].change_percent, "1Y should have data from webgia")
        # 3Y exceeds webgia range; depends on local store seeds
        # Backfill should have been called
        self.assertTrue(mock_record.called)

    @patch("gold_dashboard.repositories.history_repo.record_snapshot")
    @patch("gold_dashboard.repositories.history_repo.get_value_at")
    @patch("gold_dashboard.repositories.history_repo.requests.post")
    @patch("gold_dashboard.repositories.history_repo.requests.get")
    def test_gold_falls_back_to_chogia(
        self, mock_get: MagicMock, mock_post: MagicMock,
        mock_local: MagicMock, mock_record: MagicMock,
    ) -> None:
        """When webgia.com fails, gold should fall back to chogia.vn for 1W/1M."""
        import requests.exceptions
        # webgia.com fails
        mock_get.side_effect = requests.exceptions.ConnectionError("webgia down")

        # chogia.vn succeeds with 30 days
        now = datetime.now()
        entries = []
        for days_ago in range(30):
            dt = now - timedelta(days=29 - days_ago)
            entries.append({
                "ngay": dt.strftime("%d/%m"),
                "gia_ban": str(160000 + days_ago * 700),
                "gia_mua": str(158000 + days_ago * 700),
            })

        mock_post_response = MagicMock()
        mock_post_response.raise_for_status = MagicMock()
        mock_post_response.json.return_value = {"success": True, "data": entries}
        mock_post.return_value = mock_post_response
        mock_local.return_value = None

        repo = HistoryRepository()
        result = repo._gold_changes(Decimal("181000000"))

        self.assertEqual(result.asset_name, "gold")
        change_map = {c.period: c for c in result.changes}
        self.assertIsNotNone(change_map["1W"].change_percent, "1W from chogia fallback")
        self.assertIsNotNone(change_map["1M"].change_percent, "1M from chogia fallback")

    @patch("gold_dashboard.repositories.history_repo.record_snapshot")
    @patch("gold_dashboard.repositories.history_repo.get_value_at")
    @patch("gold_dashboard.repositories.history_repo.requests.post")
    @patch("gold_dashboard.repositories.history_repo.requests.get")
    def test_gold_falls_back_to_local_store(
        self, mock_get: MagicMock, mock_post: MagicMock,
        mock_local: MagicMock, mock_record: MagicMock,
    ) -> None:
        """When both webgia and chogia fail, gold uses local history store."""
        import requests.exceptions
        mock_get.side_effect = requests.exceptions.ConnectionError("down")
        mock_post.side_effect = requests.exceptions.ConnectionError("down")
        mock_local.return_value = Decimal("170000000")

        repo = HistoryRepository()
        result = repo._gold_changes(Decimal("181000000"))

        self.assertEqual(result.asset_name, "gold")
        self.assertEqual(len(result.changes), len(HISTORY_PERIODS))
        self.assertIn("1D", [c.period for c in result.changes])

        for change in result.changes:
            self.assertIsNotNone(change.change_percent)
            self.assertIsNotNone(change.old_value)

    @patch("gold_dashboard.repositories.history_repo.get_value_at")
    @patch("gold_dashboard.repositories.history_repo.requests.get")
    def test_bitcoin_coingecko_success(
        self, mock_get: MagicMock, mock_local: MagicMock
    ) -> None:
        """When CoinGecko returns data, Bitcoin changes should be computed from it."""
        now = datetime.now()
        # Build fake CoinGecko response with daily prices
        prices = []
        for days_ago in range(1096):
            ts_ms = (now - timedelta(days=days_ago)).timestamp() * 1000
            prices.append([ts_ms, 2000000000 + days_ago * 1000000])
        prices.reverse()

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {"prices": prices}
        mock_get.return_value = mock_response
        mock_local.return_value = None

        repo = HistoryRepository()
        result = repo._bitcoin_changes(Decimal("2600000000"))

        self.assertEqual(result.asset_name, "bitcoin")
        # At least some periods should have computed values
        has_data = any(c.change_percent is not None for c in result.changes)
        self.assertTrue(has_data)

    @patch("gold_dashboard.repositories.history_repo.get_value_at")
    @patch("gold_dashboard.repositories.history_repo.requests.get")
    def test_vn30_vps_success(
        self, mock_get: MagicMock, mock_local: MagicMock
    ) -> None:
        """When VPS API returns data, VN30 changes should be computed."""
        import time as _time

        now_ts = int(_time.time())
        timestamps = [now_ts - i * 86400 for i in range(1096)]
        timestamps.reverse()
        closes = [1200 + i * 0.1 for i in range(1096)]

        mock_response = MagicMock()
        mock_response.raise_for_status = MagicMock()
        mock_response.json.return_value = {
            "s": "ok",
            "t": timestamps,
            "c": closes,
        }
        mock_get.return_value = mock_response
        mock_local.return_value = None

        repo = HistoryRepository()
        result = repo._vn30_changes(Decimal("1300"))

        self.assertEqual(result.asset_name, "vn30")
        has_data = any(c.change_percent is not None for c in result.changes)
        self.assertTrue(has_data)


class TestUsdVndSeeds(unittest.TestCase):
    """Test USD/VND historical seed and backfill methods."""

    def setUp(self) -> None:
        self._tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        )
        self._tmp.close()
        self._patch = patch(
            "gold_dashboard.history_store.HISTORY_FILE", self._tmp.name
        )
        self._patch.start()

    def tearDown(self) -> None:
        self._patch.stop()
        if os.path.exists(self._tmp.name):
            os.unlink(self._tmp.name)

    def test_seed_values_are_sane(self) -> None:
        """All seed values should be in the expected VND/USD range."""
        for date_str, value in _USD_VND_HISTORICAL_SEEDS:
            self.assertGreater(value, Decimal("20000"), f"{date_str} too low")
            self.assertLess(value, Decimal("35000"), f"{date_str} too high")

    def test_seed_populates_local_store(self) -> None:
        """Seeding should write values retrievable from the local store."""
        HistoryRepository._seed_historical_usd_vnd()

        for date_str, expected in _USD_VND_HISTORICAL_SEEDS:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            value = get_value_at("usd_vnd", dt)
            self.assertEqual(value, expected, f"Seed {date_str} not found")

    @patch("gold_dashboard.repositories.history_repo.requests.post")
    @patch("gold_dashboard.repositories.history_repo.requests.get")
    def test_usd_vnd_changes_wires_seeds(self, mock_get: MagicMock, mock_post: MagicMock) -> None:
        """_usd_vnd_changes should call seed and return all configured periods."""
        import requests.exceptions
        mock_get.side_effect = requests.exceptions.ConnectionError("down")
        mock_post.side_effect = requests.exceptions.ConnectionError("down")

        repo = HistoryRepository()
        result = repo._usd_vnd_changes(Decimal("26500"))
        self.assertEqual(result.asset_name, "usd_vnd")
        self.assertEqual(len(result.changes), len(HISTORY_PERIODS))
        self.assertIn("1D", [c.period for c in result.changes])

    def test_backfill_usd_vnd_persists(self) -> None:
        """Backfill should write chogia.vn data into the local store."""
        rates = {
            "2025-01-15": Decimal("25900"),
            "2025-01-16": Decimal("25950"),
        }
        HistoryRepository._backfill_usd_vnd_history(rates)

        value = get_value_at("usd_vnd", datetime(2025, 1, 15))
        self.assertEqual(value, Decimal("25900"))

    def test_find_seed_rate_uses_nearest_anchor_within_window(self) -> None:
        """Nearest monthly seed should be returned when target date lacks an exact local snapshot."""
        target = datetime(2025, 2, 20)
        value = HistoryRepository._find_seed_rate(_USD_VND_HISTORICAL_SEEDS, target)
        self.assertEqual(value, Decimal("25855"))


class TestBitcoinSeeds(unittest.TestCase):
    """Test Bitcoin historical seed and backfill methods."""

    def setUp(self) -> None:
        self._tmp = tempfile.NamedTemporaryFile(
            mode="w", suffix=".json", delete=False
        )
        self._tmp.close()
        self._patch = patch(
            "gold_dashboard.history_store.HISTORY_FILE", self._tmp.name
        )
        self._patch.start()

    def tearDown(self) -> None:
        self._patch.stop()
        if os.path.exists(self._tmp.name):
            os.unlink(self._tmp.name)

    def test_seed_values_are_sane(self) -> None:
        """All seed values should be in the expected BTC/VND range (hundreds of millions to low billions)."""
        for date_str, value in _BTC_VND_HISTORICAL_SEEDS:
            self.assertGreater(value, Decimal("100000000"), f"{date_str} too low")
            self.assertLess(value, Decimal("5000000000"), f"{date_str} too high")

    def test_seed_populates_local_store(self) -> None:
        """Seeding should write values retrievable from the local store."""
        HistoryRepository._seed_historical_bitcoin()

        for date_str, expected in _BTC_VND_HISTORICAL_SEEDS:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            value = get_value_at("bitcoin", dt)
            self.assertEqual(value, expected, f"Seed {date_str} not found")

    @patch("gold_dashboard.repositories.history_repo.requests.post")
    @patch("gold_dashboard.repositories.history_repo.requests.get")
    def test_bitcoin_changes_wires_seeds(self, mock_get: MagicMock, mock_post: MagicMock) -> None:
        """_bitcoin_changes should call seed and return all configured periods."""
        import requests.exceptions
        mock_get.side_effect = requests.exceptions.ConnectionError("down")
        mock_post.side_effect = requests.exceptions.ConnectionError("down")

        repo = HistoryRepository()
        result = repo._bitcoin_changes(Decimal("2600000000000"))
        self.assertEqual(result.asset_name, "bitcoin")
        self.assertEqual(len(result.changes), len(HISTORY_PERIODS))
        self.assertIn("1D", [c.period for c in result.changes])

    def test_backfill_bitcoin_persists(self) -> None:
        """Backfill should write CoinGecko data into the local store."""
        now = datetime(2025, 6, 1)
        day_key = int(now.timestamp() / 86400)
        day_prices = {day_key: Decimal("2500000000000")}

        HistoryRepository._backfill_bitcoin_history(day_prices)

        value = get_value_at("bitcoin", now)
        self.assertIsNotNone(value)


if __name__ == "__main__":
    unittest.main()
