"""
Generate data.json for Firebase web dashboard.
Fetches data from all repositories and exports to public/data.json.
"""

import json
import sys
import warnings
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .repositories import GoldRepository, CurrencyRepository, CryptoRepository, StockRepository, HistoryRepository
from .models import DashboardData, AssetHistoricalData
from .history_store import record_snapshot

warnings.filterwarnings("ignore", message="Unverified HTTPS request")

REQUIRED_ASSETS = ("gold", "usd_vnd", "bitcoin", "vn30")


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
            'timestamp': (data.gold.timestamp.isoformat() + 'Z') if data.gold.timestamp else None
        }
    
    if data.usd_vnd:
        result['usd_vnd'] = {
            'sell_rate': float(data.usd_vnd.sell_rate) if data.usd_vnd.sell_rate else None,
            'source': data.usd_vnd.source,
            'timestamp': (data.usd_vnd.timestamp.isoformat() + 'Z') if data.usd_vnd.timestamp else None
        }
    
    if data.bitcoin:
        result['bitcoin'] = {
            'btc_to_vnd': float(data.bitcoin.btc_to_vnd) if data.bitcoin.btc_to_vnd else None,
            'source': data.bitcoin.source,
            'timestamp': (data.bitcoin.timestamp.isoformat() + 'Z') if data.bitcoin.timestamp else None
        }
    
    if data.vn30:
        result['vn30'] = {
            'index_value': float(data.vn30.index_value) if data.vn30.index_value else None,
            'change_percent': float(data.vn30.change_percent) if data.vn30.change_percent else None,
            'source': data.vn30.source,
            'timestamp': (data.vn30.timestamp.isoformat() + 'Z') if data.vn30.timestamp else None
        }
    
    # Add metadata
    result['generated_at'] = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')

    return result


def _load_previous_payload(output_file: Path) -> Optional[Dict[str, Any]]:
    """Load previously committed data.json as last-known-good candidate."""
    if not output_file.exists():
        return None

    try:
        with open(output_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def _assess_payload_health(payload: Dict[str, Any]) -> Tuple[Dict[str, Any], bool, List[str]]:
    """Assess payload quality and flag severe degradation states."""
    assets_health: Dict[str, Dict[str, Any]] = {}
    degraded_assets: List[str] = []
    severe_degradation = False

    history = payload.get('history', {})
    timeseries = payload.get('timeseries', {})

    for asset in REQUIRED_ASSETS:
        reasons: List[str] = []
        status = 'ok'
        current = payload.get(asset)

        if current is None:
            reasons.append('missing_current_section')
            severe_degradation = True
        elif asset == 'usd_vnd' and current.get('sell_rate') is None:
            reasons.append('missing_sell_rate')
            severe_degradation = True
        elif asset == 'vn30':
            source = str(current.get('source') or '').lower()
            if source.startswith('fallback'):
                reasons.append('hardcoded_fallback_source')

            vn30_series = timeseries.get('vn30') or []
            if len(vn30_series) < 2:
                reasons.append('short_timeseries')

        asset_history = history.get(asset)
        if isinstance(asset_history, list):
            missing_periods = [
                c.get('period', '?')
                for c in asset_history
                if c.get('change_percent') is None
            ]
            if missing_periods:
                reasons.append(f"missing_history:{','.join(missing_periods)}")

        if reasons:
            status = 'degraded'
            degraded_assets.append(asset)

        assets_health[asset] = {
            'status': status,
            'reasons': reasons,
            'source': current.get('source') if isinstance(current, dict) else None,
        }

    overall_status = 'degraded' if degraded_assets else 'ok'
    health = {
        'overall': overall_status,
        'assets': assets_health,
    }
    return health, severe_degradation, degraded_assets


def _restore_degraded_assets_from_lkg(
    payload: Dict[str, Any],
    previous_payload: Dict[str, Any],
    degraded_assets: List[str],
) -> List[str]:
    """Restore degraded asset blocks from previous payload when available."""
    restored_assets: List[str] = []

    for asset in degraded_assets:
        if asset not in previous_payload:
            continue

        payload[asset] = previous_payload[asset]
        restored_assets.append(asset)

        prev_history = previous_payload.get('history', {})
        if isinstance(prev_history, dict) and asset in prev_history:
            payload.setdefault('history', {})
            payload['history'][asset] = prev_history[asset]

        prev_series = previous_payload.get('timeseries', {})
        if isinstance(prev_series, dict) and asset in prev_series:
            payload.setdefault('timeseries', {})
            payload['timeseries'][asset] = prev_series[asset]

    return restored_assets


def merge_current_into_timeseries(
    timeseries: dict,
    data: DashboardData,
    date_key: Optional[str] = None,
) -> dict:
    """Upsert current snapshot values into same-day timeseries points."""
    today = date_key or datetime.now(timezone.utc).strftime('%Y-%m-%d')
    merged = {
        asset: [point for point in points if point[0] <= today]
        for asset, points in timeseries.items()
    }

    def upsert(asset_key: str, value: Optional[Decimal]) -> None:
        if value is None:
            return

        point = [today, float(value)]
        points = merged.setdefault(asset_key, [])

        for idx, existing in enumerate(points):
            if existing[0] == today:
                points[idx] = point
                break
        else:
            points.append(point)

        points.sort(key=lambda p: p[0])

    if data.gold:
        upsert('gold', data.gold.sell_price)
    if data.usd_vnd:
        upsert('usd_vnd', data.usd_vnd.sell_rate)
    if data.bitcoin:
        upsert('bitcoin', data.bitcoin.btc_to_vnd)
    if data.vn30:
        upsert('vn30', data.vn30.index_value)

    return merged


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
    
    # Resolve output path early so we can use previous payload as LKG fallback
    project_root = Path(__file__).resolve().parent.parent.parent
    public_dir = project_root / 'public'
    public_dir.mkdir(exist_ok=True)
    output_file = public_dir / 'data.json'

    previous_payload = _load_previous_payload(output_file)

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
    
    # Fetch raw time-series data for frontend charts
    timeseries = {}
    try:
        timeseries = HistoryRepository().fetch_timeseries()
        print("✓ Time-series data fetched")
    except Exception as e:
        print(f"⚠ Time-series fetch failed: {e}")
    
    # Serialize to dictionary
    json_data = serialize_data(data)
    
    # Add historical changes to output
    if history:
        json_data['history'] = _serialize_history(history)
    
    # Add time-series data for charts
    if timeseries:
        json_data['timeseries'] = merge_current_into_timeseries(timeseries, data)

    # Assess payload health and restore degraded assets from previous payload if needed
    health, severe_degradation, degraded_assets = _assess_payload_health(json_data)
    restored_assets: List[str] = []
    if severe_degradation and previous_payload is not None:
        restored_assets = _restore_degraded_assets_from_lkg(
            json_data,
            previous_payload,
            degraded_assets,
        )
        health, severe_degradation, degraded_assets = _assess_payload_health(json_data)

    health['severe_degradation'] = severe_degradation
    if restored_assets:
        health['restored_from_lkg'] = restored_assets
    json_data['health'] = health
    
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
        if restored_assets:
            print(f"  Restored from LKG: {', '.join(restored_assets)}")
        print("-" * 60)
        print()
        
        return 0
        
    except Exception as e:
        print(f"✗ Error writing data.json: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
