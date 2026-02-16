"""
Repository package for Vietnam Gold Dashboard.
Implements the Repository Pattern for data fetching.
"""

from .base import Repository
from .gold_repo import GoldRepository
from .currency_repo import CurrencyRepository
from .crypto_repo import CryptoRepository
from .stock_repo import StockRepository
from .land_repo import LandRepository
from .history_repo import HistoryRepository

__all__ = [
    'Repository',
    'GoldRepository',
    'CurrencyRepository',
    'CryptoRepository',
    'StockRepository',
    'LandRepository',
    'HistoryRepository',
]
