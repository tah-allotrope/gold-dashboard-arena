"""
Generic HTML analyzer utility to inspect DOM structure of target URLs.
"""
import requests
from bs4 import BeautifulSoup
import sys
from config import HEADERS, REQUEST_TIMEOUT

def analyze(url):
    print(f"Analyzing {url}...")
    try:
        response = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT, verify=False)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'lxml')

        print(f"Title: {soup.title.string if soup.title else 'N/A'}")

        print("\n--- Tables ---")
        tables = soup.find_all('table')
        print(f"Found {len(tables)} tables")
        for i, table in enumerate(tables):
            print(f"Table {i}: id={table.get('id')}, class={table.get('class')}")

        print("\n--- Forms ---")
        forms = soup.find_all('form')
        for i, form in enumerate(forms):
            print(f"Form {i}: action={form.get('action')}, method={form.get('method')}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        analyze(sys.argv[1])
    else:
        print("Usage: python analyze_html.py <url>")
