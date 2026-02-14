"""Regression tests for web data generation consistency."""

import unittest
from datetime import datetime, timezone
from decimal import Decimal

from gold_dashboard.generate_data import serialize_data, merge_current_into_timeseries
from gold_dashboard.models import DashboardData, GoldPrice, UsdVndRate, BitcoinPrice, Vn30Index


class TestGenerateDataSerialization(unittest.TestCase):
    """Test JSON serialization consistency for web output."""

    def test_generated_at_is_utc_with_z_suffix(self) -> None:
        data = DashboardData(
            gold=GoldPrice(
                buy_price=Decimal("100"),
                sell_price=Decimal("110"),
                source="Test",
            )
        )

        payload = serialize_data(data)

        self.assertIn("generated_at", payload)
        self.assertTrue(payload["generated_at"].endswith("Z"))

        parsed = datetime.fromisoformat(payload["generated_at"].replace("Z", "+00:00"))
        self.assertIsNotNone(parsed.tzinfo)
        self.assertEqual(parsed.tzinfo, timezone.utc)


class TestMergeCurrentIntoTimeseries(unittest.TestCase):
    """Ensure latest card values and chart values stay in sync."""

    def test_overrides_existing_today_points(self) -> None:
        today = "2026-02-14"
        timeseries = {
            "gold": [["2026-02-13", 179000000.0], [today, 181000000.0]],
            "usd_vnd": [[today, 25813.0]],
            "bitcoin": [[today, 1818718192.33]],
            "vn30": [[today, 2018.64]],
        }

        current = DashboardData(
            gold=GoldPrice(buy_price=Decimal("176000000"), sell_price=Decimal("179000000"), source="DOJI"),
            usd_vnd=UsdVndRate(sell_rate=Decimal("26591.29"), source="ExchangeRate API (est.)"),
            bitcoin=BitcoinPrice(btc_to_vnd=Decimal("1719154966.55"), source="CoinMarketCap"),
            vn30=Vn30Index(index_value=Decimal("2018.64"), source="VPS"),
        )

        merged = merge_current_into_timeseries(timeseries, current, date_key=today)

        self.assertEqual(merged["gold"][-1], [today, 179000000.0])
        self.assertEqual(merged["usd_vnd"][-1], [today, 26591.29])
        self.assertEqual(merged["bitcoin"][-1], [today, 1719154966.55])
        self.assertEqual(merged["vn30"][-1], [today, 2018.64])

    def test_appends_missing_today_points(self) -> None:
        today = "2026-02-14"
        timeseries = {
            "gold": [["2026-02-13", 179000000.0]],
            "vn30": [["2026-02-13", 2018.64]],
        }

        current = DashboardData(
            gold=GoldPrice(buy_price=Decimal("176000000"), sell_price=Decimal("179000000"), source="DOJI"),
            vn30=Vn30Index(index_value=Decimal("2018.64"), source="VPS"),
        )

        merged = merge_current_into_timeseries(timeseries, current, date_key=today)

        self.assertEqual(merged["gold"][-1], [today, 179000000.0])
        self.assertEqual(merged["vn30"][-1], [today, 2018.64])

    def test_discards_future_points_before_upsert(self) -> None:
        today = "2026-02-14"
        timeseries = {
            "gold": [["2026-02-13", 179000000.0], ["2026-02-15", 181000000.0]],
        }

        current = DashboardData(
            gold=GoldPrice(buy_price=Decimal("176000000"), sell_price=Decimal("179000000"), source="DOJI"),
        )

        merged = merge_current_into_timeseries(timeseries, current, date_key=today)

        self.assertEqual(merged["gold"][-1], [today, 179000000.0])
        self.assertNotIn(["2026-02-15", 181000000.0], merged["gold"])


if __name__ == "__main__":
    unittest.main()
