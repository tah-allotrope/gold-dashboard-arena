"""
Data models for Vietnam Gold Dashboard using dataclasses.
All models use Decimal for financial data to avoid floating-point errors.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from datetime import datetime
from typing import Optional


@dataclass
class GoldPrice:
    """Model for Vietnamese gold prices (SJC or local sources)."""
    buy_price: Decimal
    sell_price: Decimal
    source: str
    unit: str = "VND/tael"
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if self.buy_price <= 0 or self.sell_price <= 0:
            raise ValueError("Prices must be positive")


@dataclass
class UsdVndRate:
    """Model for USD/VND black market exchange rate."""
    sell_rate: Decimal
    source: str = "EGCurrency"
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if self.sell_rate <= 0:
            raise ValueError("Exchange rate must be positive")


@dataclass
class BitcoinPrice:
    """Model for Bitcoin to VND conversion rate."""
    btc_to_vnd: Decimal
    source: str = "CoinMarketCap"
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if self.btc_to_vnd <= 0:
            raise ValueError("BTC price must be positive")


@dataclass
class Vn30Index:
    """Model for VN30 stock index."""
    index_value: Decimal
    source: str = "Vietstock"
    change_percent: Optional[Decimal] = None
    timestamp: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        if self.index_value <= 0:
            raise ValueError("Index value must be positive")


@dataclass
class DashboardData:
    """Aggregated model for all dashboard data."""
    gold: Optional[GoldPrice] = None
    usd_vnd: Optional[UsdVndRate] = None
    bitcoin: Optional[BitcoinPrice] = None
    vn30: Optional[Vn30Index] = None
