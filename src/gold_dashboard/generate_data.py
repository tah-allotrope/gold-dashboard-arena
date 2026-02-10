"""
Generate data.json for Firebase web dashboard.
Fetches data from all repositories and exports to public/data.json.
"""

import json
import sys
import warnings
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from .repositories import GoldRepository, CurrencyRepository, CryptoRepository, StockRepository, HistoryRepository
from .models import DashboardData, AssetHistoricalData
from .history_store import record_snapshot

warnings.filterwarnings("ignore", message="Unverified HTTPS request")


def decimal_to_float(obj):
    """Convert Decimal objects to float for JSON serialization."""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


def fetch_all_data() -> DashboardData:
    """
    Fetch data from all repositories with error handling.
    
    Each repository is tried independently; if one fails, others continue.
    Cache decorator ensures stale data is returned if source is unavailable.
    """
    data = DashboardData()
    
    print("Fetching data from all sources...")
    
    try:
        data.gold = GoldRepository().fetch()
        print("✓ Gold price fetched")
    except Exception as e:
        print(f"⚠ Gold fetch failed: {e}")
    
    try:
        data.usd_vnd = CurrencyRepository().fetch()
        print("✓ USD/VND rate fetched")
    except Exception as e:
        print(f"⚠ USD/VND fetch failed: {e}")
    
    try:
        data.bitcoin = CryptoRepository().fetch()
        print("✓ Bitcoin price fetched")
    except Exception as e:
        print(f"⚠ Bitcoin fetch failed: {e}")
    
    try:
        data.vn30 = StockRepository().fetch()
        print("✓ VN30 index fetched")
    except Exception as e:
        print(f"⚠ VN30 fetch failed: {e}")
    
    return data


def serialize_data(data: DashboardData) -> dict:
    """Convert DashboardData to JSON-serializable dictionary."""
    result = {}
    
    if data.gold:
        result['gold'] = {
            'buy_price': float(data.gold.buy_price) if data.gold.buy_price else None,
            'sell_price': float(data.gold.sell_price) if data.gold.sell_price else None,
            'unit': data.gold.unit,
            'source': data.gold.source,
            'timestamp': data.gold.timestamp.isoformat() if data.gold.timestamp else None
        }
    
    if data.usd_vnd:
        result['usd_vnd'] = {
            'sell_rate': float(data.usd_vnd.sell_rate) if data.usd_vnd.sell_rate else None,
            'source': data.usd_vnd.source,
            'timestamp': data.usd_vnd.timestamp.isoformat() if data.usd_vnd.timestamp else None
        }
    
    if data.bitcoin:
        result['bitcoin'] = {
            'btc_to_vnd': float(data.bitcoin.btc_to_vnd) if data.bitcoin.btc_to_vnd else None,
            'source': data.bitcoin.source,
            'timestamp': data.bitcoin.timestamp.isoformat() if data.bitcoin.timestamp else None
        }
    
    if data.vn30:
        result['vn30'] = {
            'index_value': float(data.vn30.index_value) if data.vn30.index_value else None,
            'change_percent': float(data.vn30.change_percent) if data.vn30.change_percent else None,
            'source': data.vn30.source,
            'timestamp': data.vn30.timestamp.isoformat() if data.vn30.timestamp else None
        }
    
    # Add metadata
    result['generated_at'] = datetime.now().isoformat()
    
    return result


def _record_current_snapshots(data: DashboardData) -> None:
    """Persist today's values into the local history store."""
    if data.gold:
        record_snapshot("gold", data.gold.sell_price)
    if data.usd_vnd:
        record_snapshot("usd_vnd", data.usd_vnd.sell_rate)
    if data.bitcoin:
        record_snapshot("bitcoin", data.bitcoin.btc_to_vnd)
    if data.vn30:
        record_snapshot("vn30", data.vn30.index_value)


def _serialize_history(history: dict) -> dict:
    """Convert AssetHistoricalData dict to JSON-serializable format."""
    result = {}
    for asset_key, asset_data in history.items():
        changes = []
        for c in asset_data.changes:
            changes.append({
                'period': c.period,
                'old_value': float(c.old_value) if c.old_value is not None else None,
                'new_value': float(c.new_value) if c.new_value is not None else None,
                'change_percent': float(c.change_percent) if c.change_percent is not None else None,
            })
        result[asset_key] = changes
    return result


def main():
    """Main function to generate data.json."""
    print("=" * 60)
    print("Vietnam Gold Dashboard - Data Generator")
    print("=" * 60)
    print()
    
    # Fetch data
    data = fetch_all_data()
    
    # Record current values into local history store for future lookups
    _record_current_snapshots(data)
    
    # Fetch historical changes (external APIs + local store)
    history = {}
    try:
        history = HistoryRepository().fetch_changes(data)
        print("✓ Historical changes fetched")
    except Exception as e:
        print(f"⚠ Historical changes fetch failed: {e}")
    
    # Serialize to dictionary
    json_data = serialize_data(data)
    
    # Add historical changes to output
    if history:
        json_data['history'] = _serialize_history(history)
    
    # Ensure public directory exists (relative to project root, not package)
    project_root = Path(__file__).resolve().parent.parent.parent
    public_dir = project_root / 'public'
    public_dir.mkdir(exist_ok=True)
    
    # Write to data.json
    output_file = public_dir / 'data.json'
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2, default=decimal_to_float)
        
        print()
        print(f"✓ Data successfully written to {output_file}")
        print(f"✓ Generated at: {json_data['generated_at']}")
        print()
        
        # Print summary
        print("Data Summary:")
        print("-" * 60)
        if 'gold' in json_data:
            print(f"  Gold: {json_data['gold']['source']}")
        if 'usd_vnd' in json_data:
            print(f"  USD/VND: {json_data['usd_vnd']['source']}")
        if 'bitcoin' in json_data:
            print(f"  Bitcoin: {json_data['bitcoin']['source']}")
        if 'vn30' in json_data:
            print(f"  VN30: {json_data['vn30']['source']}")
        print("-" * 60)
        print()
        
        return 0
        
    except Exception as e:
        print(f"✗ Error writing data.json: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
