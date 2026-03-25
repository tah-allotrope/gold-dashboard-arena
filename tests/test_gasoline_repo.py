import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import patch
import requests

from gold_dashboard.models import GasolinePrice
from gold_dashboard.repositories.gasoline_repo import GasolineRepository
from gold_dashboard.config import GASOLINE_MIN_VALID_VND, GASOLINE_MAX_VALID_VND
from gold_dashboard.utils import _deserialize_from_cache


def test_extract_grade_price_dot_thousands():
    text = "Xăng RON 95-III: 22.500 đồng/lít. Xăng E5 RON 92: 22.100 đồng."
    val = GasolineRepository._extract_grade_price(text, "RON 95-III")
    assert val == Decimal("22500")


def test_extract_grade_price_no_separator():
    text = "RON 95-III 22500 VND E5 RON 92 22100"
    val = GasolineRepository._extract_grade_price(text, "RON 95-III")
    assert val == Decimal("22500")


def test_extract_grade_price_returns_none_for_out_of_range():
    text = "RON 95-III: 999 đồng"
    val = GasolineRepository._extract_grade_price(text, "RON 95-III")
    assert val is None


def test_extract_grade_price_returns_none_when_label_absent():
    text = "Diesel 0.05S: 20.000 đồng"
    val = GasolineRepository._extract_grade_price(text, "RON 95-III")
    assert val is None


@patch("gold_dashboard.repositories.gasoline_repo.requests.get")
@patch("gold_dashboard.repositories.gasoline_repo.Path.exists")
def test_fetch_falls_back_to_hardcoded_when_all_sources_fail(mock_exists, mock_get):
    mock_get.side_effect = requests.exceptions.RequestException("network down")
    mock_exists.return_value = False

    repo = GasolineRepository()
    result = GasolineRepository.fetch.__wrapped__(repo)

    assert result.ron95_price >= Decimal("10000")
    assert result.unit == "VND/liter"
    assert "Fallback" in result.source or "(seed)" in result.source


def test_gasoline_price_model_rejects_nonpositive():
    with pytest.raises(ValueError):
        GasolinePrice(ron95_price=Decimal("0"), source="test", timestamp=datetime.now())

    with pytest.raises(ValueError):
        GasolinePrice(
            ron95_price=Decimal("-1000"), source="test", timestamp=datetime.now()
        )


def test_gasoline_price_model_accepts_valid():
    price = GasolinePrice(
        ron95_price=Decimal("22500"),
        e5_ron92_price=Decimal("22100"),
        source="test",
        timestamp=datetime.now(),
    )
    assert price.ron95_price == Decimal("22500")
    assert price.e5_ron92_price == Decimal("22100")
    assert price.unit == "VND/liter"


def test_deserialize_cached_gasoline_price_returns_model():
    cached_obj = {
        "__dataclass__": "GasolinePrice",
        "data": {
            "ron95_price": {"__decimal__": "25570"},
            "e5_ron92_price": {"__decimal__": "22500"},
            "source": "xangdau.net",
            "unit": "VND/liter",
            "timestamp": {"__datetime__": "2026-03-25T06:00:00"},
        },
    }

    result = _deserialize_from_cache(cached_obj)

    assert isinstance(result, GasolinePrice)
    assert result.ron95_price == Decimal("25570")
    assert result.e5_ron92_price == Decimal("22500")
