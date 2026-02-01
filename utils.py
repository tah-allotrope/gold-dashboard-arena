<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/utils.py
"""
Utility functions for Vietnam Gold Dashboard.
Includes Vietnamese number sanitization and caching decorator.
"""

import os
import json
import time
from decimal import Decimal, InvalidOperation
from functools import wraps
from typing import Optional, Callable, Any, TypeVar
from datetime import datetime
import requests.exceptions

from config import CACHE_DIR, CACHE_TTL_SECONDS

T = TypeVar('T')


def sanitize_vn_number(text: str) -> Optional[Decimal]:
    """
    Convert Vietnamese or international number format to Decimal.
    
    Handles two formats:
    - Vietnamese: '.' for thousands (e.g., 80.000.000), ',' for decimal (e.g., 1.234,56)
    - International: ',' for thousands (e.g., 2,029.81), '.' for decimal
    
    Args:
        text: String containing formatted number
        
    Returns:
        Decimal representation or None if unparseable
        
    Examples:
        >>> sanitize_vn_number("25.500.000,50")
        Decimal('25500000.50')
        >>> sanitize_vn_number("2,029.81")
        Decimal('2029.81')
        >>> sanitize_vn_number("80.000.000")
        Decimal('80000000')
    """
    if not text or not isinstance(text, str):
        return None
    
    try:
        cleaned = text.strip()
        cleaned = ''.join(c for c in cleaned if c.isdigit() or c in '.,')
        
        if not cleaned:
            return None
        
        dot_count = cleaned.count('.')
        comma_count = cleaned.count(',')
        
        if comma_count == 0 and dot_count >= 2:
            cleaned = cleaned.replace('.', '')
        elif comma_count >= 1 and dot_count == 1:
            if cleaned.rfind(',') < cleaned.rfind('.'):
                cleaned = cleaned.replace(',', '')
            else:
                cleaned = cleaned.replace(',', '').replace('.', '')
                return None
        elif comma_count == 1 and dot_count == 0:
            cleaned = cleaned.replace(',', '.')
        elif comma_count == 0 and dot_count == 1:
            pass
        elif comma_count >= 2:
            cleaned = cleaned.replace(',', '')
        else:
            cleaned = cleaned.replace('.', '').replace(',', '.')
        
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None


def _get_cache_path(cache_key: str) -> str:
    """Generate cache file path for a given key."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, f"{cache_key}.json")


def _read_cache(cache_key: str) -> Optional[dict]:
    """Read cache data if it exists and is valid."""
    cache_path = _get_cache_path(cache_key)
    
    if not os.path.exists(cache_path):
        return None
    
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
            
        timestamp = cache_data.get('timestamp', 0)
        age_seconds = time.time() - timestamp
        
        if age_seconds < CACHE_TTL_SECONDS:
            return cache_data.get('data')
        
        return None
    except (json.JSONDecodeError, IOError):
        return None


def _write_cache(cache_key: str, data: Any) -> None:
    """Write data to cache with current timestamp."""
    cache_path = _get_cache_path(cache_key)
    
    try:
        cache_data = {
            'timestamp': time.time(),
            'data': data
        }
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2, default=str)
    except IOError:
        pass


def _read_stale_cache(cache_key: str) -> Optional[dict]:
    """Read cache data regardless of TTL (for fallback purposes)."""
    cache_path = _get_cache_path(cache_key)
    
    if not os.path.exists(cache_path):
        return None
    
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        return cache_data.get('data')
    except (json.JSONDecodeError, IOError):
        return None


def cached(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator that caches function results with TTL-based expiration.
    
    Behavior:
    - Returns cached value if it exists and is < CACHE_TTL_SECONDS old
    - Otherwise calls the wrapped function
    - If function raises requests.exceptions.RequestException, returns stale cache
    - Caches successful results with timestamp
    
    Args:
        func: Function to decorate (should return pydantic model or dict)
        
    Returns:
        Decorated function with caching behavior
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        cache_key = f"{func.__name__}"
        
        cached_data = _read_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        try:
            result = func(*args, **kwargs)
            _write_cache(cache_key, result)
            return result
        except requests.exceptions.RequestException:
            stale_data = _read_stale_cache(cache_key)
            if stale_data is not None:
                return stale_data
            raise
    
    return wrapper
=======
"""
Utility functions for Vietnam Gold Dashboard.
Includes Vietnamese number sanitization and caching decorator.
"""

import os
import json
import time
from decimal import Decimal, InvalidOperation
from functools import wraps
from typing import Optional, Callable, Any, TypeVar
from datetime import datetime
from dataclasses import asdict, is_dataclass
import requests.exceptions

from config import CACHE_DIR, CACHE_TTL_SECONDS

T = TypeVar('T')


def sanitize_vn_number(text: str) -> Optional[Decimal]:
    """
    Convert Vietnamese or international number format to Decimal.
    
    Handles two formats:
    - Vietnamese: '.' for thousands (e.g., 80.000.000), ',' for decimal (e.g., 1.234,56)
    - International: ',' for thousands (e.g., 2,029.81), '.' for decimal
    
    Args:
        text: String containing formatted number
        
    Returns:
        Decimal representation or None if unparseable
        
    Examples:
        >>> sanitize_vn_number("25.500.000,50")
        Decimal('25500000.50')
        >>> sanitize_vn_number("2,029.81")
        Decimal('2029.81')
        >>> sanitize_vn_number("80.000.000")
        Decimal('80000000')
    """
    if not text or not isinstance(text, str):
        return None
    
    try:
        cleaned = text.strip()
        cleaned = ''.join(c for c in cleaned if c.isdigit() or c in '.,')
        
        if not cleaned:
            return None
        
        dot_count = cleaned.count('.')
        comma_count = cleaned.count(',')
        
        if comma_count == 0 and dot_count >= 2:
            cleaned = cleaned.replace('.', '')
        elif comma_count >= 1 and dot_count == 1:
            if cleaned.rfind(',') < cleaned.rfind('.'):
                cleaned = cleaned.replace(',', '')
            else:
                cleaned = cleaned.replace(',', '').replace('.', '')
                return None
        elif comma_count == 1 and dot_count == 0:
            cleaned = cleaned.replace(',', '.')
        elif comma_count == 0 and dot_count == 1:
            pass
        elif comma_count >= 2:
            cleaned = cleaned.replace(',', '')
        else:
            cleaned = cleaned.replace('.', '').replace(',', '.')
        
        return Decimal(cleaned)
    except (InvalidOperation, ValueError):
        return None


def _get_cache_path(cache_key: str) -> str:
    """Generate cache file path for a given key."""
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, f"{cache_key}.json")


def _deserialize_from_cache(obj: Any) -> Any:
    """Reconstruct dataclass objects from cached JSON data."""
    if isinstance(obj, dict):
        if '__dataclass__' in obj:
            # Import models to get dataclass types
            from models import GoldPrice, UsdVndRate, BitcoinPrice, Vn30Index
            
            class_map = {
                'GoldPrice': GoldPrice,
                'UsdVndRate': UsdVndRate,
                'BitcoinPrice': BitcoinPrice,
                'Vn30Index': Vn30Index
            }
            
            class_name = obj['__dataclass__']
            data_dict = obj['data']
            
            # Deserialize nested objects
            for key, value in data_dict.items():
                data_dict[key] = _deserialize_from_cache(value)
            
            # Reconstruct the dataclass
            if class_name in class_map:
                return class_map[class_name](**data_dict)
        elif '__decimal__' in obj:
            return Decimal(obj['__decimal__'])
        elif '__datetime__' in obj:
            return datetime.fromisoformat(obj['__datetime__'])
        else:
            # Recursively deserialize nested dicts
            return {k: _deserialize_from_cache(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_deserialize_from_cache(item) for item in obj]
    return obj


def _read_cache(cache_key: str) -> Optional[dict]:
    """Read cache data if it exists and is valid."""
    cache_path = _get_cache_path(cache_key)
    
    if not os.path.exists(cache_path):
        return None
    
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
            
        timestamp = cache_data.get('timestamp', 0)
        age_seconds = time.time() - timestamp
        
        if age_seconds < CACHE_TTL_SECONDS:
            serialized_data = cache_data.get('data')
            return _deserialize_from_cache(serialized_data)
        
        return None
    except (json.JSONDecodeError, IOError):
        return None


def _serialize_for_cache(obj: Any) -> Any:
    """Convert dataclass objects to JSON-serializable format."""
    if is_dataclass(obj):
        return {
            '__dataclass__': obj.__class__.__name__,
            'data': asdict(obj)
        }
    elif isinstance(obj, Decimal):
        return {'__decimal__': str(obj)}
    elif isinstance(obj, datetime):
        return {'__datetime__': obj.isoformat()}
    return obj


def _write_cache(cache_key: str, data: Any) -> None:
    """Write data to cache with current timestamp."""
    cache_path = _get_cache_path(cache_key)
    
    try:
        # Convert dataclass to dict for JSON serialization
        serialized_data = _serialize_for_cache(data)
        
        cache_data = {
            'timestamp': time.time(),
            'data': serialized_data
        }
        
        with open(cache_path, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2, default=_serialize_for_cache)
    except IOError:
        pass


def _read_stale_cache(cache_key: str) -> Optional[dict]:
    """Read cache data regardless of TTL (for fallback purposes)."""
    cache_path = _get_cache_path(cache_key)
    
    if not os.path.exists(cache_path):
        return None
    
    try:
        with open(cache_path, 'r', encoding='utf-8') as f:
            cache_data = json.load(f)
        serialized_data = cache_data.get('data')
        return _deserialize_from_cache(serialized_data)
    except (json.JSONDecodeError, IOError):
        return None


def cached(func: Callable[..., T]) -> Callable[..., T]:
    """
    Decorator that caches function results with TTL-based expiration.
    
    Behavior:
    - Returns cached value if it exists and is < CACHE_TTL_SECONDS old
    - Otherwise calls the wrapped function
    - If function raises requests.exceptions.RequestException, returns stale cache
    - Caches successful results with timestamp
    
    Args:
        func: Function to decorate (should return pydantic model or dict)
        
    Returns:
        Decorated function with caching behavior
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> T:
        # Include class name if method is bound to an instance
        if args and hasattr(args[0], '__class__'):
            cache_key = f"{args[0].__class__.__name__}_{func.__name__}"
        else:
            cache_key = f"{func.__name__}"
        
        cached_data = _read_cache(cache_key)
        if cached_data is not None:
            return cached_data
        
        try:
            result = func(*args, **kwargs)
            _write_cache(cache_key, result)
            return result
        except requests.exceptions.RequestException:
            stale_data = _read_stale_cache(cache_key)
            if stale_data is not None:
                return stale_data
            raise
    
    return wrapper
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-b41d3eed/utils.py
