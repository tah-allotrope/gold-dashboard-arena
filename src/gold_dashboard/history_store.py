"""
Local history store for Vietnam Gold Dashboard.
Persists asset snapshots to a JSON file so we can compute historical changes
for assets without external historical APIs (e.g., SJC Gold).
"""

import json
import os
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, List, Dict, Any

from .config import CACHE_DIR


HISTORY_FILE = os.path.join(CACHE_DIR, "history.json")

# Maximum age tolerance when looking up a historical value.
# If the closest snapshot is more than this many days away from the target,
# we consider it "not available".
MAX_LOOKUP_TOLERANCE_DAYS = 3


def _load_history() -> Dict[str, List[Dict[str, Any]]]:
    """Load the full history file from disk. Returns empty dict if missing."""
    if not os.path.exists(HISTORY_FILE):
        return {}
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def _save_history(data: Dict[str, List[Dict[str, Any]]]) -> None:
    """Persist the full history dict to disk."""
    os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except IOError:
        pass


def record_snapshot(asset: str, value: Decimal, timestamp: Optional[datetime] = None) -> None:
    """
    Append a data-point for *asset* into the local history file.

    Deduplicates by date: if a snapshot already exists for the same calendar
    day, the existing entry is updated instead of creating a duplicate.

    Args:
        asset: Asset key, e.g. "gold", "usd_vnd", "bitcoin", "vn30".
        value: The representative Decimal value to record.
        timestamp: When the value was observed (defaults to now).
    """
    if timestamp is None:
        timestamp = datetime.now()

    history = _load_history()
    entries: List[Dict[str, Any]] = history.get(asset, [])

    date_str = timestamp.strftime("%Y-%m-%d")
    iso_str = timestamp.isoformat()

    # Update existing entry for the same day, or append new one
    for entry in entries:
        if entry.get("date") == date_str:
            entry["value"] = str(value)
            entry["timestamp"] = iso_str
            break
    else:
        entries.append({
            "date": date_str,
            "value": str(value),
            "timestamp": iso_str,
        })

    # Keep entries sorted by date ascending
    entries.sort(key=lambda e: e["date"])

    history[asset] = entries
    _save_history(history)


def get_value_at(asset: str, target_date: datetime) -> Optional[Decimal]:
    """
    Return the recorded value closest to *target_date* for *asset*.

    If the closest snapshot is more than MAX_LOOKUP_TOLERANCE_DAYS away,
    returns None (data not available).

    Args:
        asset: Asset key, e.g. "gold".
        target_date: The date we want a value for.

    Returns:
        Decimal value or None if no suitable snapshot exists.
    """
    history = _load_history()
    entries = history.get(asset, [])

    if not entries:
        return None

    target_str = target_date.strftime("%Y-%m-%d")
    best_entry: Optional[Dict[str, Any]] = None
    best_delta: Optional[timedelta] = None

    for entry in entries:
        entry_date = datetime.strptime(entry["date"], "%Y-%m-%d")
        delta = abs(entry_date - target_date)
        if best_delta is None or delta < best_delta:
            best_delta = delta
            best_entry = entry

    if best_entry is None or best_delta is None:
        return None

    if best_delta > timedelta(days=MAX_LOOKUP_TOLERANCE_DAYS):
        return None

    try:
        return Decimal(best_entry["value"])
    except Exception:
        return None


def get_all_entries(asset: str) -> List[Dict[str, Any]]:
    """Return all recorded snapshots for an asset (sorted by date)."""
    history = _load_history()
    return history.get(asset, [])
