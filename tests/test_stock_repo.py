"""Regression tests for StockRepository fallback behavior."""

import unittest
from decimal import Decimal
from unittest.mock import MagicMock, patch

from gold_dashboard.repositories.stock_repo import StockRepository


class TestStockRepositoryFallbacks(unittest.TestCase):
    """Ensure VN30 fetch order prefers real VPS last-close over static fallback."""

    @patch("gold_dashboard.repositories.stock_repo.time.sleep", return_value=None)
    @patch("gold_dashboard.repositories.stock_repo.requests.get")
    def test_uses_vps_last_close_when_short_window_is_empty(
        self,
        mock_get: MagicMock,
        _mock_sleep: MagicMock,
    ) -> None:
        """When 7-day VPS window fails, repository should use 30-day VPS last close."""
        # Vietstock fails first
        vietstock_fail = MagicMock()
        vietstock_fail.raise_for_status.side_effect = ValueError("vietstock parse fail")

        # First three VPS attempts (7-day) fail with empty data
        vps_empty = MagicMock()
        vps_empty.raise_for_status = MagicMock()
        vps_empty.json.return_value = {"s": "no_data", "c": []}

        # Next VPS call for 30-day fallback succeeds
        vps_ok = MagicMock()
        vps_ok.raise_for_status = MagicMock()
        vps_ok.json.return_value = {"s": "ok", "c": [1995.12, 2002.34, 2018.64]}

        mock_get.side_effect = [
            vietstock_fail,
            vps_empty,
            vps_empty,
            vps_empty,
            vps_ok,
        ]

        repo = StockRepository()
        result = StockRepository.fetch.__wrapped__(repo)

        self.assertEqual(result.source, "VPS (last close)")
        self.assertEqual(result.index_value, Decimal("2018.64"))
        self.assertIsNotNone(result.change_percent)

    @patch("gold_dashboard.repositories.stock_repo.time.sleep", return_value=None)
    @patch("gold_dashboard.repositories.stock_repo.requests.get")
    def test_falls_back_to_static_only_after_all_sources_fail(
        self,
        mock_get: MagicMock,
        _mock_sleep: MagicMock,
    ) -> None:
        """Static fallback should be used only when every source fails."""
        import requests

        mock_get.side_effect = requests.exceptions.RequestException("network down")

        repo = StockRepository()
        result = StockRepository.fetch.__wrapped__(repo)

        self.assertEqual(result.source, "Fallback (Scraping Failed)")
        self.assertEqual(result.index_value, Decimal("1950.00"))


if __name__ == "__main__":
    unittest.main()
