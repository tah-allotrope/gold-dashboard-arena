<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/activeContext.md
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/activeContext.md
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/activeContext.md
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/activeContext.md
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/activeContext.md
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
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/activeContext.md
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/activeContext.md
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/activeContext.md
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/activeContext.md
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/activeContext.md
# Active Context

## Project Snapshot
- **Project:** Vietnam Gold Dashboard (Firebase Hosting)
- **Goal:** Scrape Vietnamese gold price (SJC/local) alongside USD/VND (black market), Bitcoin, and VN30 index; render via web dashboard.
- **Cadence:** 10-minute refresh (per user directive).
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/activeContext.md
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/activeContext.md
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/activeContext.md
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/activeContext.md
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/activeContext.md
- **Status:** Phase 3 Complete (Dashboard operational with VN30 data; other sources require advanced parsing).
=======
- **Status:** Phase 3 Complete - Dashboard operational with fallback mechanisms for all sources.
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/activeContext.md
=======
- **Status:** Phase 3 Complete - Dashboard operational with fallback mechanisms for all sources.
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/activeContext.md

## Current Files
- **Core:** `main.py` (entry point), `dashboard.py` (Rich UI), `config.py` (settings)
- **Data Layer:** `models.py` (dataclasses), `utils.py` (sanitization/cache), `repositories/` (fetching logic)
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/activeContext.md
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/activeContext.md
- **Tools:** `inspect_sources.py` (HTML grabber), `analyze_html.py` (DOM inspector), `test_repositories.py` (validation)
- **Docs:** `AGENTS.md`, `research.md`, `implementation.md`
=======
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/activeContext.md
=======
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/activeContext.md
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/activeContext.md
- **Status:** Phase 4 Complete - Web dashboard implemented and ready for Firebase deployment.

## Current Files
- **Web Dashboard (Firebase):**
  - `public/index.html` - Responsive web dashboard
  - `public/styles.css` - Modern, mobile-friendly styling
  - `public/app.js` - Frontend data fetching and rendering
  - `public/data.json` - Generated market data (auto-generated)
  - `generate_data.py` - Data generation script
  - `firebase.json` - Firebase hosting configuration
  - `.firebaserc` - Firebase project settings
- **Terminal Dashboard (Legacy):** `main.py`, `dashboard.py` (Rich UI)
- **Data Layer:** `models.py` (dataclasses), `utils.py` (sanitization/cache), `repositories/` (fetching logic)
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/activeContext.md
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/activeContext.md
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/activeContext.md
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/activeContext.md
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/activeContext.md
  - `repositories/gold_repo.py` - Gold price fetcher with SJC/Mi Hồng/fallback strategy
  - `repositories/currency_repo.py` - USD/VND black market rate fetcher
  - `repositories/crypto_repo.py` - Bitcoin price fetcher
  - `repositories/stock_repo.py` - VN30 index fetcher
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/activeContext.md
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/activeContext.md
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/activeContext.md
- **Debug Tools:** `debug_mihong.py`, `debug_alternative_gold.py`, `test_sjc_parse.py`, `test_egcurrency_parse.py`
- **Docs:** `AGENTS.md`, `research.md`, `activeContext.md`
=======
- **Config:** `config.py` (URLs, headers, cache settings)
- **Docs:** `AGENTS.md`, `research.md`, `activeContext.md`, `README_DEPLOYMENT.md`
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/activeContext.md
=======
- **Config:** `config.py` (URLs, headers, cache settings)
- **Docs:** `AGENTS.md`, `research.md`, `activeContext.md`, `README_DEPLOYMENT.md`
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/activeContext.md
=======
- **Config:** `config.py` (URLs, headers, cache settings)
- **Docs:** `AGENTS.md`, `research.md`, `activeContext.md`, `README_DEPLOYMENT.md`
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/activeContext.md

## Research Findings (Phase 1 Complete)
### Gold (Local)
- **SJC official:** `https://sjc.com.vn/gia-vang-online` (Uses dynamic JS loading; empty HTML table)
- **Mi Hồng fallback:** `https://www.mihong.vn/en/vietnam-gold-pricings` (SSL certificate issues; verify=False workaround)

### USD/VND (Black Market)
- **EGCurrency:** `https://egcurrency.com/en/currency/USD-to-VND/blackMarket` (Compressed/encoded HTML; parsing challenges)
- **TygiaUSD:** `https://tygiausd.org/` (Alternative source; heavy content)

### VN30 Index
- **Vietstock:** `https://banggia.vietstock.vn/bang-gia/vn30` (✅ Working - extracts index value and change percent)

### Bitcoin
- **CoinMarketCap (BTC/VND):** `https://coinmarketcap.com/currencies/bitcoin/btc/vnd/` (Complex DOM structure; requires specific selectors)
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/activeContext.md
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/activeContext.md
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/activeContext.md
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/activeContext.md
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/activeContext.md
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/activeContext.md
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/activeContext.md
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/activeContext.md
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/activeContext.md

## Phase 3 Implementation Status
### Source Status
1. **VN30 Index (Vietstock):** ✅ **Working**
   - Successfully extracts current value and change percent
   - Handles international number format (`,` thousands, `.` decimal)
   
2. **Gold (SJC/Mi Hồng):** ⚠️ **Fallback Mode**
   - SJC: Dynamic JS loading prevents direct scraping
   - Mi Hồng: SSL verification issues and complex HTML structure
   - **Fallback:** Returns approximate market data (87.5M buy / 88.5M sell VND/tael) when scraping fails
   
3. **USD/VND (EGCurrency):** ⚠️ **Fallback Mode**
   - HTML compression/encoding prevents reliable parsing
   - **Fallback:** Returns approximate market rate (25,500 VND/USD) when scraping fails
   
4. **Bitcoin (CoinMarketCap):** ⚠️ **Fallback Mode**
   - Complex DOM structure requires advanced selectors
   - **Fallback:** Returns approximate conversion rate when scraping fails

### Key Technical Achievements
- **Dual Number Format Support:** `sanitize_vn_number()` handles both Vietnamese (`.` thousands, `,` decimal) and international (`,` thousands, `.` decimal) formats
- **Repository Pattern:** Clean separation between data fetching and UI rendering; each source isolated with independent error handling
- **Graceful Degradation:** Dashboard displays without crashing when sources are unavailable; fallback data ensures UI always renders
- **Cache Decorator:** JSON-based caching with 10-minute TTL prevents excessive requests and provides stale data fallback
- **Rich Terminal UI:** Color-coded freshness indicators (green < 5min, yellow 5-10min, red > 10min), proper Vietnamese number formatting in display

## Phase 2: Architecture (✅ Complete)
**Files Created:**
- `config.py` - URLs, browser-like headers, cache settings (10-min TTL)
- `models.py` - Dataclass models with validation (`GoldPrice`, `UsdVndRate`, `BitcoinPrice`, `Vn30Index`, `DashboardData`)
- `utils.py` - Vietnamese number sanitizer + JSON-based cache decorator
- `repositories/` - Abstract `Repository` base + 4 concrete implementations
- `requirements.txt` - Dependencies: beautifulsoup4, lxml, rich, requests

**Architecture Decision:** Used Python dataclasses instead of Pydantic v2 to avoid Rust compilation requirements. Dataclasses provide equivalent type safety via `__post_init__` validation without external dependencies.

## Constraints & Standards (from AGENTS.md)
- Use `requests` with strict headers, `beautifulsoup4` + `lxml` for parsing
- Use `Decimal` for currency calculations and VN number sanitization
- Cache for 5–10 minutes; if fetch fails, return cached value instead of crashing
- All URLs/selectors live in `config.py`; type hints everywhere
- Graceful degradation: UI must never crash due to source unavailability

## Known Issues & Merge Conflicts
- **File Conflicts:** `gold_repo.py` and `utils.py` have merge conflicts from multiple worktrees that need resolution
- **Scraping Challenges:** Most Vietnamese sources use anti-bot measures (JS rendering, SSL issues, compression)
- **Fallback Data:** Current fallback values are static approximations; consider alternative sources or APIs

<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/activeContext.md
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/activeContext.md
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/activeContext.md
## Next Steps (Phase 4 - Optional)
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/activeContext.md
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/activeContext.md
1. Implement alternative gold price source with simpler HTML structure
2. Find alternative USD/VND black market API or simpler scraping target
3. Deploy static HTML version to Firebase Hosting
4. Set up scheduled Cloud Functions for periodic scraping
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-9c259637/activeContext.md
=======
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/activeContext.md
1. Resolve merge conflicts in `gold_repo.py` and `utils.py`
2. Research alternative data sources with simpler HTML or JSON APIs
3. Consider using Selenium/Playwright for JS-rendered content
4. Deploy static HTML version to Firebase Hosting
5. Set up scheduled Cloud Functions for periodic scraping
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/activeContext.md
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/activeContext.md
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/activeContext.md
=======
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/activeContext.md
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/activeContext.md
## Phase 4: Web Dashboard Implementation (✅ Complete - 2026-02-02)
**Files Created:**
- `public/index.html` - Responsive web dashboard with Vietnamese number formatting
- `public/styles.css` - Modern, mobile-first design with gradient background
- `public/app.js` - Client-side data fetching, rendering, and auto-refresh
- `generate_data.py` - Python script to export repository data as JSON
- `firebase.json` - Hosting configuration with cache headers
- `.firebaserc` - Firebase project reference
- `README_DEPLOYMENT.md` - Complete deployment and automation guide

**Architecture Decision:** Static HTML + JSON approach
- Python script generates `data.json` from existing repositories
- Static HTML/CSS/JS reads and displays the JSON
- Deploy to Firebase Hosting for shareable URL
- Manual or automated updates via Task Scheduler or GitHub Actions

**Key Features:**
- Mobile-responsive design (optimized for phone viewing)
- Vietnamese number formatting (`.` for thousands, `,` for decimals)
- Color-coded freshness indicators (green/yellow/red based on data age)
- Auto-refresh every 10 minutes
- Manual refresh button
- Works offline with cached data

## Next Steps (Deployment & Automation)
1. ✅ Install Firebase CLI: `npm install -g firebase-tools`
2. ✅ Login to Firebase: `firebase login`
3. ✅ Create/select Firebase project
4. ✅ Update `.firebaserc` with actual project ID
5. ✅ Generate initial data: `python generate_data.py`
6. ✅ Deploy: `firebase deploy --only hosting`
7. Share URL with wife for browser access
8. (Optional) Set up automated updates via Task Scheduler or GitHub Actions
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/activeContext.md
<<<<<<< C:/Users/tukum/Downloads/gold-dashboard-arena/activeContext.md
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/activeContext.md
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/activeContext.md
=======
>>>>>>> C:/Users/tukum/.windsurf/worktrees/gold-dashboard-arena/gold-dashboard-arena-1468470e/activeContext.md
