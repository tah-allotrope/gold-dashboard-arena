"""Tests for LandRepository scraping and fallback behavior."""

import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

from gold_dashboard.repositories.land_repo import LandRepository


class TestLandRepository(unittest.TestCase):
    """Validate Hong Bang listing parsing and resilient fallback behavior."""

    def test_extracts_unit_price_from_hong_bang_snippets(self) -> None:
        repo = LandRepository()
        html = """
        <html><body>
            <h3>Nha mat tien Hong Bang 4x12 - 5 tang - 12 Ty 5 TL</h3>
            <h3>Ban nha mat tien Hong Bang - 12 x20m- Gia chi 45 ty TL</h3>
            <h3>Nha mat tien duong khac 3x10 - 3 ty</h3>
        </body></html>
        """

        prices = repo._extract_hong_bang_unit_prices(html)

        self.assertGreaterEqual(len(prices), 2)
        # 12.5B / 48m2
        self.assertIn(Decimal("260416666.67"), prices)
        # 45B / 240m2
        self.assertIn(Decimal("187500000.00"), prices)

    @patch("gold_dashboard.repositories.land_repo.requests.get")
    def test_fetch_uses_fallback_when_source_fails(self, mock_get: MagicMock) -> None:
        import requests

        mock_get.side_effect = requests.exceptions.RequestException("network down")

        repo = LandRepository()
        result = LandRepository.fetch.__wrapped__(repo)

        self.assertEqual(result.source, "Fallback (Manual estimate)")
        self.assertEqual(result.price_per_m2, Decimal("255000000"))
        self.assertEqual(result.location, "Hong Bang Street, District 11, Ho Chi Minh City")


if __name__ == "__main__":
    unittest.main()
