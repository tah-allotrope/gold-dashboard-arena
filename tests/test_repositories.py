import pytest
from repositories import GoldRepository, CurrencyRepository, CryptoRepository, StockRepository
from decimal import Decimal

def test_gold_repo():
    repo = GoldRepository()
    data = repo.fetch()
    assert data is not None
    assert data.buy_price > 0
    assert data.sell_price > 0
    assert isinstance(data.buy_price, Decimal)
    assert data.source != "Fallback (Scraping Failed)"

def test_currency_repo():
    repo = CurrencyRepository()
    data = repo.fetch()
    assert data is not None
    assert data.sell_rate > 20000
    assert isinstance(data.sell_rate, Decimal)

def test_crypto_repo():
    repo = CryptoRepository()
    data = repo.fetch()
    assert data is not None
    assert data.btc_to_vnd > 1000000000
    assert isinstance(data.btc_to_vnd, Decimal)

def test_stock_repo():
    repo = StockRepository()
    data = repo.fetch()
    assert data is not None
    assert data.index_value > 500
    assert isinstance(data.index_value, Decimal)
