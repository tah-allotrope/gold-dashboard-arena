"""
Test script to verify all repositories fetch data correctly.
"""

import warnings
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

from repositories import GoldRepository, CurrencyRepository, CryptoRepository, StockRepository
from datetime import datetime


def test_repository(name, repo_class):
    """Test a single repository and print results."""
    print(f"\n{'='*60}")
    print(f"Testing {name}")
    print('='*60)
    
    try:
        repo = repo_class()
        data = repo.fetch()
        print(f"✓ Success!")
        print(f"  Data: {data}")
        print(f"  Timestamp: {data.timestamp}")
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback
        traceback.print_exc()


def main():
    print("Vietnam Gold Dashboard - Repository Tests")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_repository("Gold Repository", GoldRepository)
    test_repository("Currency Repository", CurrencyRepository)
    test_repository("Crypto Repository", CryptoRepository)
    test_repository("Stock Repository", StockRepository)
    
    print(f"\n{'='*60}")
    print("Testing complete")
    print('='*60)


if __name__ == "__main__":
    main()
