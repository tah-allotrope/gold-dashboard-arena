"""Regression tests for web data generation consistency."""

import unittest
from datetime import datetime, timezone
from decimal import Decimal

from gold_dashboard.generate_data import (
    serialize_data,
    merge_current_into_timeseries,
    _assess_payload_health,
    _record_current_snapshots,
    _restore_degraded_assets_from_lkg,
)
from gold_dashboard.models import (
    DashboardData,
    GoldPrice,
    UsdVndRate,
    BitcoinPrice,
    Vn30Index,
    LandPrice,
    GasolinePrice,
)
from unittest.mock import patch


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

    def test_serialize_data_includes_land_asset(self) -> None:
        data = DashboardData(
            gold=GoldPrice(
                buy_price=Decimal("176000000"),
                sell_price=Decimal("180000000"),
                source="DOJI",
            ),
            usd_vnd=UsdVndRate(
                sell_rate=Decimal("25000"),
                source="chogia.vn",
            ),
            bitcoin=BitcoinPrice(
                btc_to_vnd=Decimal("2000000000"),
                source="CoinMarketCap",
            ),
            land=LandPrice(
                price_per_m2=Decimal("184210526"),
                source="alonhadat.com.vn",
                location="Hong Bang Street, District 11, Ho Chi Minh City",
            ),
        )

        payload = serialize_data(data)
        self.assertIn("land", payload)

        land = payload["land"]
        self.assertEqual(
            land["location"], "Hong Bang Street, District 11, Ho Chi Minh City"
        )
        self.assertEqual(land["unit"], "VND/m2")
        self.assertEqual(land["source"], "alonhadat.com.vn")
        self.assertEqual(land["price_per_m2"], 184210526.0)
        self.assertIn("timestamp", land)

    def test_serialize_data_omits_land_when_missing(self) -> None:
        payload = serialize_data(DashboardData())
        self.assertNotIn("land", payload)


class TestMergeCurrentIntoTimeseries(unittest.TestCase):
    """Ensure latest card values and chart values stay in sync."""

    def test_overrides_existing_today_points(self) -> None:
        today = "2026-02-14"
        timeseries = {
            "gold": [["2026-02-13", 179000000.0], [today, 181000000.0]],
            "usd_vnd": [[today, 25813.0]],
            "bitcoin": [[today, 1818718192.33]],
            "vn30": [[today, 2018.64]],
            "land": [[today, 255000000.0]],
        }

        current = DashboardData(
            gold=GoldPrice(
                buy_price=Decimal("176000000"),
                sell_price=Decimal("179000000"),
                source="DOJI",
            ),
            usd_vnd=UsdVndRate(
                sell_rate=Decimal("26591.29"), source="ExchangeRate API (est.)"
            ),
            bitcoin=BitcoinPrice(
                btc_to_vnd=Decimal("1719154966.55"), source="CoinMarketCap"
            ),
            vn30=Vn30Index(index_value=Decimal("2018.64"), source="VPS"),
            land=LandPrice(
                price_per_m2=Decimal("184210526"),
                source="alonhadat.com.vn",
                location="Hong Bang Street, District 11, Ho Chi Minh City",
            ),
        )

        merged = merge_current_into_timeseries(timeseries, current, date_key=today)

        self.assertEqual(merged["gold"][-1], [today, 179000000.0])
        self.assertEqual(merged["usd_vnd"][-1], [today, 26591.29])
        self.assertEqual(merged["bitcoin"][-1], [today, 1719154966.55])
        self.assertEqual(merged["vn30"][-1], [today, 2018.64])
        self.assertEqual(merged["land"][-1], [today, 184210526.0])

    def test_appends_missing_today_points(self) -> None:
        today = "2026-02-14"
        timeseries = {
            "gold": [["2026-02-13", 179000000.0]],
            "vn30": [["2026-02-13", 2018.64]],
        }

        current = DashboardData(
            gold=GoldPrice(
                buy_price=Decimal("176000000"),
                sell_price=Decimal("179000000"),
                source="DOJI",
            ),
            vn30=Vn30Index(index_value=Decimal("2018.64"), source="VPS"),
            land=LandPrice(
                price_per_m2=Decimal("184210526"),
                source="alonhadat.com.vn",
                location="Hong Bang Street, District 11, Ho Chi Minh City",
            ),
        )

        merged = merge_current_into_timeseries(timeseries, current, date_key=today)

        self.assertEqual(merged["gold"][-1], [today, 179000000.0])
        self.assertEqual(merged["vn30"][-1], [today, 2018.64])
        self.assertEqual(merged["land"][-1], [today, 184210526.0])

    def test_discards_future_points_before_upsert(self) -> None:
        today = "2026-02-14"
        timeseries = {
            "gold": [["2026-02-13", 179000000.0], ["2026-02-15", 181000000.0]],
        }

        current = DashboardData(
            gold=GoldPrice(
                buy_price=Decimal("176000000"),
                sell_price=Decimal("179000000"),
                source="DOJI",
            ),
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
            "land": {"price_per_m2": 184210526.0, "source": "alonhadat.com.vn"},
            "gasoline": {
                "ron95_price": 25570.0,
                "source": "xangdau.net",
                "timestamp": datetime.now(timezone.utc)
                .isoformat()
                .replace("+00:00", "Z"),
            },
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

        self.assertFalse(severe)
        self.assertIn("vn30", degraded_assets)
        self.assertEqual(health["assets"]["vn30"]["status"], "degraded")
        self.assertIn("hardcoded_fallback_source", health["assets"]["vn30"]["reasons"])

    def test_assess_payload_health_flags_missing_land_as_severe(self) -> None:
        payload = {
            "gold": {"source": "DOJI"},
            "usd_vnd": {"sell_rate": 26550.0, "source": "chogia.vn"},
            "bitcoin": {"source": "CoinMarketCap"},
            "vn30": {"index_value": 2020.12, "source": "VPS"},
            "history": {},
            "timeseries": {},
        }

        health, severe, degraded_assets = _assess_payload_health(payload)

        self.assertTrue(severe)
        self.assertIn("land", degraded_assets)
        self.assertIn("missing_current_section", health["assets"]["land"]["reasons"])

    def test_assess_payload_health_flags_seed_gasoline_as_severe(self) -> None:
        payload = {
            "gold": {"source": "DOJI"},
            "usd_vnd": {"sell_rate": 26550.0, "source": "chogia.vn"},
            "bitcoin": {"source": "CoinMarketCap"},
            "vn30": {"index_value": 2020.12, "source": "VPS"},
            "land": {"price_per_m2": 184210526.0, "source": "homedy.com"},
            "gasoline": {
                "ron95_price": 25570.0,
                "source": "Petrolimex (seed)",
                "timestamp": "2026-03-01T00:00:00Z",
            },
            "history": {
                "gasoline": [
                    {"period": "1W", "change_percent": 13.64},
                ]
            },
            "timeseries": {
                "gasoline": [["2026-03-01", 25570.0]],
            },
        }

        health, severe, degraded_assets = _assess_payload_health(payload)

        self.assertTrue(severe)
        self.assertIn("gasoline", degraded_assets)
        self.assertIn("seed_source", health["assets"]["gasoline"]["reasons"])
        self.assertIn("stale_timestamp", health["assets"]["gasoline"]["reasons"])

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

        restored = _restore_degraded_assets_from_lkg(
            payload, previous_payload, ["vn30"]
        )

        self.assertEqual(restored, ["vn30"])
        self.assertEqual(payload["vn30"]["source"], "VPS")
        self.assertEqual(payload["history"]["vn30"][0]["change_percent"], 1.23)
        self.assertEqual(len(payload["timeseries"]["vn30"]), 2)

    def test_restore_degraded_assets_from_lkg_skips_degraded_previous_asset(
        self,
    ) -> None:
        payload = {
            "gasoline": {
                "ron95_price": 25570.0,
                "source": "Fallback (Manual estimate)",
                "timestamp": "2026-03-25T00:00:00Z",
            },
            "history": {"gasoline": [{"period": "1W", "change_percent": None}]},
            "timeseries": {"gasoline": [["2026-03-25", 25570.0]]},
        }
        previous_payload = {
            "gold": {"source": "DOJI"},
            "usd_vnd": {"sell_rate": 26550.0, "source": "chogia.vn"},
            "bitcoin": {"source": "CoinMarketCap"},
            "vn30": {"index_value": 2020.12, "source": "VPS"},
            "land": {"price_per_m2": 184210526.0, "source": "homedy.com"},
            "gasoline": {
                "ron95_price": 25570.0,
                "source": "Petrolimex (seed)",
                "timestamp": "2026-03-01T00:00:00Z",
            },
            "history": {"gasoline": [{"period": "1W", "change_percent": 13.64}]},
            "timeseries": {"gasoline": [["2026-03-01", 25570.0]]},
        }

        restored = _restore_degraded_assets_from_lkg(
            payload, previous_payload, ["gasoline"]
        )

        self.assertEqual(restored, [])
        self.assertEqual(payload["gasoline"]["source"], "Fallback (Manual estimate)")

    @patch("gold_dashboard.generate_data.record_snapshot")
    def test_record_current_snapshots_skips_seed_gasoline(self, mock_record) -> None:
        data = DashboardData(
            gasoline=GasolinePrice(
                ron95_price=Decimal("25570"),
                e5_ron92_price=Decimal("22500"),
                source="Petrolimex (seed)",
                timestamp=datetime(2026, 3, 1, 0, 0, 0),
            )
        )

        _record_current_snapshots(data)

        mock_record.assert_not_called()


if __name__ == "__main__":
    unittest.main()
