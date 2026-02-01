<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/activeContext.md
# Active Context

## Project Snapshot
- **Project:** Vietnam Gold Dashboard (Firebase Hosting only)
- **Goal:** Scrape Vietnamese gold price (SJC/local) alongside USD/VND (black market), Bitcoin, and VN30 index; render via `rich` dashboard.
- **Cadence:** 10-minute refresh (per user directive).

## Current Files
- **AGENTS.md:** Canonical rules, workflow, and tech stack.
- **research.md:** Source candidates and access notes.
- **Plan:** `C:\Users\tukum\.windsurf\plans\dashboard-plan-d96f4c.md` (phased plan).

## Research Findings (Phase 1 Complete)
### Gold (Local)
- **SJC official:** `https://sjc.com.vn/gia-vang-online` (HTML page; legacy textContent endpoints unstable or blocked).
- **Mi Hồng fallback:** `https://www.mihong.vn/en/vietnam-gold-pricings` (current price sections for gold types).

### USD/VND (Black Market)
- **EGCurrency:** `https://egcurrency.com/en/currency/USD-to-VND/blackMarket` (sell price visible in HTML).
- **TygiaUSD:** `https://tygiausd.org/` (heavy content; needs direct HTML inspection if used).

### VN30 Index
- **Vietstock:** `https://banggia.vietstock.vn/bang-gia/vn30` (VN30-INDEX line visible in page text; may be dynamic in production).

### Bitcoin
- **CoinMarketCap (BTC/VND):** `https://coinmarketcap.com/currencies/bitcoin/btc/vnd/` (conversion rate text available).

## Constraints & Standards (from AGENTS.md)
- Use `requests` with strict headers, `beautifulsoup4` + `lxml` for parsing.
- Use `Decimal` for currency calculations and VN number sanitization.
- Cache for 5–10 minutes; if fetch fails, return cached value instead of crashing.
- All URLs/selectors live in `config.py`; type hints everywhere.

## Next Steps (Phase 2)
1. Define `config.py` with URLs, headers, selectors, cache TTL.
2. Draft pydantic models and repository interfaces.
3. Implement normalization utilities and cache decorator.
4. Build fetchers, then rich UI, then sanity-check script.
=======
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
3. **USD/VND (EGCurrency):** ⚠️ **Issues**
   - HTML is compressed/encoded; standard parsing failed.
4. **Bitcoin (CoinMarketCap):** ⚠️ **Issues**
   - Complex DOM structure; needs specific selector refinement.

### Key Technical Achievements
- **Dual Number Format Support:** `sanitize_vn_number()` handles both Vietnamese (`.` thousands, `,` decimal) and international (`,` thousands, `.` decimal) formats.
- **Repository Pattern:** Clean separation between data fetching and UI rendering; each source isolated with independent error handling.
- **Graceful Degradation:** Dashboard displays without crashing when sources are unavailable; cache decorator provides stale data fallback.
- **Rich Terminal UI:** Color-coded freshness indicators (green < 5min, yellow 5-10min, red > 10min), proper Vietnamese number formatting in display.

## Phase 2: Architecture (✅ Complete - 2026-02-01)
**Files Created:**
- `config.py` - URLs, browser-like headers, cache settings (10-min TTL)
- `models.py` - Dataclass models with validation (`GoldPrice`, `UsdVndRate`, `BitcoinPrice`, `Vn30Index`, `DashboardData`)
- `utils.py` - Vietnamese number sanitizer + JSON-based cache decorator
- `repositories/` - Abstract `Repository` base + 4 concrete implementations
- `requirements.txt` - Dependencies: beautifulsoup4, lxml, rich, requests, diskcache

**Architecture Decision:** Replaced Pydantic v2 with Python dataclasses to avoid Rust compilation requirements on Python 3.14. Dataclasses provide equivalent type safety via `__post_init__` validation without external dependencies.

## Constraints & Standards (from AGENTS.md)
- Use `requests` with strict headers, `beautifulsoup4` + `lxml` for parsing.
- Use `Decimal` for currency calculations and VN number sanitization.
- Cache for 5–10 minutes; if fetch fails, return cached value instead of crashing.
- All URLs/selectors live in `config.py`; type hints everywhere.

## Next Steps (Phase 4 - Optional)
1. Implement alternative gold price source with simpler HTML structure
2. Find alternative USD/VND black market API or simpler scraping target
3. Deploy static HTML version to Firebase Hosting
4. Set up scheduled Cloud Functions for periodic scraping
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-9c259637/activeContext.md
