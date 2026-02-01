from bs4 import BeautifulSoup
from utils import sanitize_vn_number
import re

with open('.cache/egcurrency_20260201_220147.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'lxml')
text = soup.get_text()
lines = [line.strip() for line in text.split('\n') if line.strip()]

print("Looking for rate patterns...")
for i, line in enumerate(lines):
    if any(keyword in line.lower() for keyword in ['sell', 'rate', 'black', 'market']):
        context = lines[max(0, i-2):min(len(lines), i+5)]
        print(f"\nContext around '{line}':")
        for j, ctx_line in enumerate(context):
            print(f"  {j}: {ctx_line[:100]}")
            
numbers = re.findall(r'\d{2,3}[.,]\d{3}', text)
print(f"\nVN-formatted numbers found: {numbers[:20]}")
