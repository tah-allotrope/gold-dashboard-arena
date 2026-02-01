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
VIETSTOCK_URL = "https://banggia.vietstock.vn/bang-gia/vn30"
COINMARKETCAP_BTC_VND_URL = "https://coinmarketcap.com/currencies/bitcoin/btc/vnd/"
COINGECKO_API_URL = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin&vs_currencies=vnd"

REQUEST_TIMEOUT = 10

CACHE_DIR = ".cache"
