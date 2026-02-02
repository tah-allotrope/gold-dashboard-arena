"""
Test alternative gold price sources with simpler HTML structures.
"""
import requests
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

from config import HEADERS, REQUEST_TIMEOUT
from utils import sanitize_vn_number

# Alternative sources
SOURCES = {
    "PNJ": "https://www.pnj.com.vn/blog/gia-vang/",
    "DOJI": "https://www.doji.vn/gia-vang-hom-nay.html",
    "24H": "https://www.24h.com.vn/gia-vang-hom-nay-c425.html",
}

def test_source(name, url):
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print('='*60)
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, verify=False)
        response.raise_for_status()
        
        print(f"Status: {response.status_code}")
        print(f"Content-Type: {response.headers.get('Content-Type', 'unknown')}")
        print(f"Content length: {len(response.content)} bytes")
        
        # Quick parse
        soup = BeautifulSoup(response.content, 'lxml')
        text = soup.get_text()
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Look for gold-related keywords and prices
        keywords = ['SJC', 'vàng', 'gold', 'mua', 'buy', 'bán', 'sell']
        found_lines = []
        
        for i, line in enumerate(lines):
            if any(kw.lower() in line.lower() for kw in keywords):
                # Check if there's a price nearby
                for j in range(max(0, i-2), min(len(lines), i+3)):
                    price = sanitize_vn_number(lines[j])
                    if price and 1000000 < price < 100000000:
                        found_lines.append((i, line, lines[j], price))
                        break
        
        if found_lines:
            print(f"\nFound {len(found_lines)} potential gold prices:")
            for idx, (line_num, context, price_text, price_val) in enumerate(found_lines[:5]):
                print(f"  {idx+1}. Line {line_num}: {context[:50]}...")
                print(f"     Price text: {price_text} -> {price_val:,.0f}")
        else:
            print("\nNo gold prices found in expected range")
            
    except Exception as e:
        print(f"ERROR: {e}")

if __name__ == "__main__":
    for name, url in SOURCES.items():
        test_source(name, url)
