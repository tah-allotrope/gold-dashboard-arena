"""Regression tests for web data generation consistency."""

import unittest
from datetime import datetime, timezone
from decimal import Decimal

from gold_dashboard.generate_data import (
    serialize_data,
    merge_current_into_timeseries,
    _assess_payload_health,
    _restore_degraded_assets_from_lkg,
)
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

class TestPayloadHealthAndLkg(unittest.TestCase):
    """Validate payload quality assessment and LKG restoration behavior."""

    def test_assess_payload_health_flags_severe_vn30_degradation(self) -> None:
        payload = {
            "gold": {"source": "DOJI"},
            "usd_vnd": {"sell_rate": 26550.0, "source": "chogia.vn"},
            "bitcoin": {"source": "CoinMarketCap"},
            "vn30": {"index_value": 1950.0, "source": "Fallback (Scraping Failed)"},
            "history": {
                "vn30": [
                    {"period": "1W", "change_percent": None},
                ]
            },
            "timeseries": {
                "vn30": [["2026-02-14", 1950.0]],
            },
        }

        health, severe, degraded_assets = _assess_payload_health(payload)

        self.assertTrue(severe)
        self.assertIn("vn30", degraded_assets)
        self.assertEqual(health["assets"]["vn30"]["status"], "degraded")
        self.assertIn("hardcoded_fallback_source", health["assets"]["vn30"]["reasons"])

    def test_restore_degraded_assets_from_lkg_replaces_blocks(self) -> None:
        payload = {
            "vn30": {"index_value": 1950.0, "source": "Fallback (Scraping Failed)"},
            "history": {"vn30": [{"period": "1W", "change_percent": None}]},
            "timeseries": {"vn30": [["2026-02-14", 1950.0]]},
        }
        previous_payload = {
            "vn30": {"index_value": 2018.64, "source": "VPS"},
            "history": {"vn30": [{"period": "1W", "change_percent": 1.23}]},
            "timeseries": {"vn30": [["2026-02-13", 2000.0], ["2026-02-14", 2018.64]]},
        }

        restored = _restore_degraded_assets_from_lkg(payload, previous_payload, ["vn30"])

        self.assertEqual(restored, ["vn30"])
        self.assertEqual(payload["vn30"]["source"], "VPS")
        self.assertEqual(payload["history"]["vn30"][0]["change_percent"], 1.23)
        self.assertEqual(len(payload["timeseries"]["vn30"]), 2)


if __name__ == "__main__":
    unittest.main()
