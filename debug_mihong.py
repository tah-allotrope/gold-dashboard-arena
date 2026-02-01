"""
Debug script to inspect Mi Hồng HTML structure and test gold price extraction.
"""
import requests
from bs4 import BeautifulSoup
import warnings
warnings.filterwarnings("ignore", message="Unverified HTTPS request")

from config import MIHONG_URL, HEADERS, REQUEST_TIMEOUT
from utils import sanitize_vn_number

def inspect_mihong():
    print("Fetching Mi Hồng HTML...")
    response = requests.get(
        MIHONG_URL,
        headers=HEADERS,
        timeout=REQUEST_TIMEOUT,
        verify=False
    )
    response.raise_for_status()
    
    soup = BeautifulSoup(response.content, 'lxml')
    
    # Save HTML for inspection
    with open('.cache/mihong_debug.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print("Saved HTML to .cache/mihong_debug.html")
    
    # Inspect tables
    print("\n=== TABLES ===")
    tables = soup.find_all('table')
    print(f"Found {len(tables)} tables")
    
    for i, table in enumerate(tables):
        print(f"\n--- Table {i} ---")
        rows = table.find_all('tr')
        print(f"Rows: {len(rows)}")
        
        for j, row in enumerate(rows[:10]):  # First 10 rows
            cells = row.find_all(['td', 'th'])
            cell_texts = [cell.get_text(strip=True) for cell in cells]
            if cell_texts:
                print(f"  Row {j}: {cell_texts}")
                
                # Check for SJC
                if any('SJC' in text for text in cell_texts):
                    print(f"    ^^^ FOUND SJC ROW ^^^")
                    # Try to extract prices
                    for k, text in enumerate(cell_texts):
                        price = sanitize_vn_number(text)
                        if price and price > 1000000:
                            print(f"    Column {k}: {text} -> {price}")
    
    # Inspect text content
    print("\n=== TEXT CONTENT (lines with SJC) ===")
    text = soup.get_text()
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    for i, line in enumerate(lines):
        if 'SJC' in line or 'sjc' in line.lower():
            context_start = max(0, i-2)
            context_end = min(len(lines), i+10)
            print(f"\nFound SJC at line {i}:")
            for j in range(context_start, context_end):
                marker = ">>> " if j == i else "    "
                print(f"{marker}{j}: {lines[j]}")

if __name__ == "__main__":
    import os
    os.makedirs('.cache', exist_ok=True)
    inspect_mihong()
