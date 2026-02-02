# Active Context

## Project Snapshot
- **Project:** Vietnam Gold Dashboard (Firebase Hosting only)
- **Goal:** Scrape Vietnamese gold price (SJC/local) alongside USD/VND (black market), Bitcoin, and VN30 index; render via `rich` dashboard.
- **Cadence:** 10-minute refresh (per user directive).
- **Status:** Phase 3 Complete (Dashboard operational with VN30 data; other sources require advanced parsing).

## Current Files
- **Core:** `main.py` (entry point), `dashboard.py` (Rich UI), `config.py` (settings)
- **Data Layer:** `models.py` (dataclasses), `utils.py` (sanitization/cache), `repositories/` (fetching logic)
- **Tools:** `inspect_sources.py` (HTML grabber), `analyze_html.py` (DOM inspector), `test_repositories.py` (validation)
- **Docs:** `AGENTS.md`, `research.md`, `implementation.md`

## Phase 3 Implementation Results
### Source Status
1. **VN30 Index (Vietstock):** ✅ **Working**
   - Extracts current value (`2,029.81`) and change percent.
   - Handles mixed number formats (International `.` for decimals).
2. **Gold (SJC/Mi Hồng):** ⚠️ **Partial/Blocked**
   - SJC: Uses dynamic JS loading (empty HTML table).
   - Mi Hồng: SSL certificate verification issues (workaround implemented but brittle).
3. **USD/VND (EGCurrency):** ✅ **Working** (after Brotli fix)
   - Extracts current sell price from EGCurrency.
4. **Bitcoin (CoinMarketCap):** ✅ **Working**
   - Extracts BTC to VND conversion rate.

### Key Technical Achievements
- **Dual Number Format Support:** `sanitize_vn_number()` handles both Vietnamese (`.` thousands, `,` decimal) and international (`,` thousands, `.` decimal) formats.
- **Repository Pattern:** Clean separation between data fetching and UI rendering; each source isolated with independent error handling.
- **Graceful Degradation:** Dashboard displays without crashing when sources are unavailable; cache decorator provides stale data fallback.
- **Rich Terminal UI:** Color-coded freshness indicators (green < 5min, yellow 5-10min, red > 10min), proper Vietnamese number formatting in display.

## Architecture Decision
Replaced Pydantic v2 with Python dataclasses to avoid Rust compilation requirements on Python 3.14. Dataclasses provide equivalent type safety via `__post_init__` validation without external dependencies.

## Constraints & Standards (from AGENTS.md)
- Use `requests` with strict headers, `beautifulsoup4` + `lxml` for parsing.
- Use `Decimal` for currency calculations and VN number sanitization.
- Cache for 5–10 minutes; if fetch fails, return cached value instead of crashing.
- All URLs/selectors live in `config.py`; type hints everywhere.

## Next Steps
1. Improve Gold price scraping source.
2. Refine `cached` decorator to handle parsing errors.
3. Ensure overall system stability and test coverage.
