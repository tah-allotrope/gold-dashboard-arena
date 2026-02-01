"""
Analyze saved HTML files to identify parsing strategies.
"""
from bs4 import BeautifulSoup
import re
from utils import sanitize_vn_number

def analyze_sjc():
    print("\n=== Analyzing SJC HTML ===")
    with open('.cache/sjc_20260201_220142.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'lxml')
    
    tables = soup.find_all('table')
    print(f"Found {len(tables)} tables")
    
    for i, table in enumerate(tables[:3]):
        rows = table.find_all('tr')
        print(f"\nTable {i} ({len(rows)} rows):")
        for j, row in enumerate(rows[:5]):
            cells = [td.get_text(strip=True) for td in row.find_all(['td', 'th'])]
            if cells:
                print(f"  Row {j}: {cells}")

def analyze_egcurrency():
    print("\n=== Analyzing EGCurrency HTML ===")
    with open('.cache/egcurrency_20260201_220147.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'lxml')
    
    text = soup.get_text()
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    for i, line in enumerate(lines):
        if 'sell' in line.lower() or 'rate' in line.lower() or 'vnd' in line.lower():
            context = lines[max(0, i-2):min(len(lines), i+3)]
            print(f"Found potential rate context: {context}")
            break
    
    numbers = re.findall(r'\d{1,3}(?:[.,]\d{3})+', text)
    print(f"\nSample Vietnamese-formatted numbers: {numbers[:10]}")

def analyze_vietstock():
    print("\n=== Analyzing Vietstock HTML ===")
    with open('.cache/vietstock_20260201_220149.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'lxml')
    
    text = soup.get_text()
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    for i, line in enumerate(lines):
        if 'vn30' in line.lower() and 'index' in line.lower():
            context = lines[max(0, i-2):min(len(lines), i+5)]
            print(f"Found VN30 context: {context}")
            break

def analyze_coinmarketcap():
    print("\n=== Analyzing CoinMarketCap HTML ===")
    with open('.cache/coinmarketcap_20260201_220151.html', 'r', encoding='utf-8') as f:
        html = f.read()
    
    soup = BeautifulSoup(html, 'lxml')
    
    price_elements = soup.find_all(class_=re.compile(r'price', re.I))
    print(f"Found {len(price_elements)} elements with 'price' in class")
    
    for elem in price_elements[:5]:
        text = elem.get_text(strip=True)
        if text and any(char.isdigit() for char in text):
            print(f"  Price element: {text[:100]}")

if __name__ == "__main__":
    analyze_sjc()
    analyze_egcurrency()
    analyze_vietstock()
    analyze_coinmarketcap()
