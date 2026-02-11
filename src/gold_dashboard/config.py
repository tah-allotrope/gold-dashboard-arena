"""
Configuration file for Vietnam Gold Dashboard.
Contains URLs, HTTP headers, CSS selectors, and cache settings.
"""

CACHE_TTL_SECONDS = 600

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9,vi;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Cache-Control": "max-age=0",
}

SJC_URL = "https://sjc.com.vn/gia-vang-online"
MIHONG_URL = "https://www.mihong.vn/en/vietnam-gold-pricings"
EGCURRENCY_URL = "https://egcurrency.com/en/currency/USD-to-VND/blackMarket"

DOJI_API_URL = "http://giavang.doji.vn/api/giavang/?api_key=258fbd2a72ce8481089d88c678e9fe4f"
CHOGIA_AJAX_URL = "https://chogia.vn/wp-admin/admin-ajax.php"
VIETSTOCK_URL = "https://banggia.vietstock.vn/bang-gia/vn30"
CAFEF_URL = "https://s.cafef.vn/hastc/VN30-INDEX.chn"

# Fallback APIs (international-friendly, work from any IP)
OPEN_ER_API_URL = "https://open.er-api.com/v6/latest/USD"
VPS_VN30_API_URL = "https://histdatafeed.vps.com.vn/tradingview/history?symbol=VN30&resolution=D"

COINMARKETCAP_BTC_VND_URL = "https://coinmarketcap.com/currencies/bitcoin/btc/vnd/"
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=vnd"

# Historical data APIs
COINGECKO_MARKET_CHART_URL = "https://api.coingecko.com/api/v3/coins/bitcoin/market_chart?vs_currency=vnd"
WEBGIA_GOLD_1Y_URL = "https://webgia.com/gia-vang/sjc/bieu-do-1-nam.html"

# Period label -> number of days for historical lookups
HISTORY_PERIODS = {"1W": 7, "1M": 30, "1Y": 365, "3Y": 1095}

REQUEST_TIMEOUT = 10

CACHE_DIR = ".cache"
