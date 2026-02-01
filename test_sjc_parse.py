from bs4 import BeautifulSoup

with open('.cache/sjc_20260201_220142.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'lxml')
table = soup.find('table', class_='sjc-table-show-price-online')

if table:
    print("Table found!")
    tbody = table.find('tbody')
    if tbody:
        rows = tbody.find_all('tr')
        print(f"Found {len(rows)} rows")
        for i, row in enumerate(rows[:5]):
            cells = [td.text.strip() for td in row.find_all('td')]
            print(f"Row {i}: {cells}")
    else:
        print("No tbody, checking direct tr")
        rows = table.find_all('tr')
        print(f"Found {len(rows)} direct rows")
        for i, row in enumerate(rows[:5]):
            cells = [td.text.strip() for td in row.find_all(['td', 'th'])]
            print(f"Row {i}: {cells}")
else:
    print("Table not found - trying all tables")
    tables = soup.find_all('table')
    print(f"Total tables: {len(tables)}")
