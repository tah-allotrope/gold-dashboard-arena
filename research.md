# Research Notes

This document captures candidate sources, access notes, and selector/API hints for the Vietnam Gold Dashboard.

## SJC / Local Gold Prices
### Primary: DOJI API (VERIFIED WORKING - Feb 2026)
- URL: `http://giavang.doji.vn/api/giavang/?api_key=258fbd2a72ce8481089d88c678e9fe4f`
- Format: XML
- Response structure:
  ```xml
  <GoldList>
    <DGPlist>
      <Row Name='DOJI HCM lẻ' Key='dojihanoile' Sell='17,540' Buy='17,240' />
      ...
    </DGPlist>
  </GoldList>
  ```
- Notes: Prices are in units of 10,000 VND. E.g., `Sell='17,540'` = 175,400,000 VND/tael.
- Target row: `Name` containing "HCM" and "lẻ" (retail price in Ho Chi Minh City).
- API key is publicly embedded in their website; may rotate periodically.

### Secondary: Mi Hồng (local gold prices)
- URL: https://www.mihong.vn/en/vietnam-gold-pricings
- Notes: Page exposes sections for current price (Gold Type: SJC, 999, etc.) and time ranges. In code, parse the table structure (may require inspecting live HTML via requests).

### Tertiary: SJC (official) - CURRENTLY BROKEN
- URL: https://sjc.com.vn/gia-vang-online
- Notes: Page loads prices via JavaScript; initial HTML has empty tables. Legacy `textContent.php` endpoints are blocked/unstable.

## USD/VND (Black Market)
### Primary: chogia.vn AJAX (VERIFIED WORKING - Feb 2026)
- URL: `POST https://chogia.vn/wp-admin/admin-ajax.php`
- Request body: `action=load_gia_ngoai_te_cho_do_thi&ma=USD`
- Content-Type: `application/x-www-form-urlencoded`
- Format: JSON
- Response structure:
  ```json
  {
    "success": true,
    "data": [
      {"ngay_text": "06/02", "gia_ban": "26495", "gia_mua": "26635", "ngay": "2026-02-06"},
      ...
    ]
  }
  ```
- Notes: Returns ~30 days of historical data. Take the last entry for the latest rate.
- `gia_ban` = sell rate (what you get when selling USD), `gia_mua` = buy rate (what you pay to buy USD).
- Values are in VND per 1 USD (e.g., 26495 = 26,495 VND).

### Secondary: EGCurrency - INACCURATE
- URL: https://egcurrency.com/en/currency/USD-to-VND/blackMarket
- Notes: Despite the "Black Market" label, returns values closer to official bank rates (~25,339) rather than true black market rates (~26,495). Use as fallback only.

### Deprecated: TygiaUSD
- URL: https://tygiausd.org/
- Notes: Domain is parked/sold. No longer functional.

## VN30 Index
- URL: https://banggia.vietstock.vn/bang-gia/vn30
- Notes: Page exposes index line for "VN30-INDEX" with value and delta in plain text. Parse the VN30 row or index line. If dynamic in production, may require finding the API behind the page.

## Bitcoin (BTC/VND)
- URL: https://coinmarketcap.com/currencies/bitcoin/btc/vnd/
- Notes: Page contains BTC to VND conversion text. Parsing may require targeting specific DOM nodes; consider using CMC only for crypto (allowed by domain rules).

## Anti-Bot / Headers
- Use strict browser-like headers for every request (User-Agent, Accept, Accept-Language, Referer when needed).
- Set timeouts and retry with backoff; if a scrape fails, return cached values.

## Next Research Actions
1. Confirm SJC HTML structure in live requests; if blocked, switch primary to Mi Hồng for local gold price.
2. Inspect EGCurrency and Vietstock HTML to pin exact CSS selectors.
3. Verify whether Vietstock exposes a JSON/CSV API for VN30 index.
