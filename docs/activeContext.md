# Active Context

## Project Snapshot
- **Project:** Vietnam Gold Dashboard (Firebase Hosting)
- **Goal:** Scrape Vietnamese gold price (SJC/local) alongside USD/VND (black market), Bitcoin, and VN30 index; render via web dashboard.
- **Status:** Phase 7 Complete - Frontend bug fixes & consistency pass.
- **Cadence:** 30-minute refresh (GitHub Actions cron `*/30`).

## Current Files
- **Web Dashboard (Firebase):**
  - `public/index.html` - Responsive web dashboard with Vietnamese number formatting.
  - `public/styles.css` - Modern, mobile-friendly styling.
  - `public/app.js` - Frontend data fetching and rendering.
  - `public/data.json` - Generated market data (auto-generated).
  - `firebase.json` - Firebase hosting configuration.
  - `.firebaserc` - Firebase project settings.
- **Terminal Dashboard (Legacy):** `src/gold_dashboard/main.py`, `src/gold_dashboard/dashboard.py` (Rich UI).
- **Data Layer:** 
  - `src/gold_dashboard/models.py` - Dataclasses for market data.
  - `src/gold_dashboard/utils.py` - Sanitization and caching logic.
  - `src/gold_dashboard/repositories/` - Data fetching logic for Gold, Currency, Crypto, and Stocks.
- **Data Generation:** `src/gold_dashboard/generate_data.py` - Static export for Firebase.
- **Tests:** `tests/` - Repository and parse tests.
- **Scripts:** `scripts/` - Debug and HTML analysis scripts.
- **Docs:** `AGENTS.md`, `docs/research.md`, `docs/activeContext.md`, `README.md`.

## Implementation Status
- **VN30 Index (Vietstock):** Working. Extracts value and change percentage. History via VPS TradingView API (1W/1M/1Y/3Y).
- **Gold (DOJI API):** Working. SJC retail prices via DOJI XML API (primary).
- **Gold History:** Working. webgia.com (primary, ~1Y real SJC data), chogia.vn (fallback, ~30 days), local store seeded with verified news prices (3Y).
- **USD/VND (chogia.vn):** Working. Black market rates via AJAX JSON (primary). History via chogia.vn (~30 days) + local store seeded with verified black-market rates (2023–2025) for 1Y/3Y.
- **Bitcoin (CoinMarketCap):** Working. History via CoinGecko market_chart API (1W/1M/1Y) + local store seeded with verified BTC/VND prices (2022–2025) for 3Y.
- **GitHub Actions:** Working. Cron schedule (`*/30 * * * *`) successfully generating data and deploying to Firebase.
- **History Store:** `.cache/history.json` — local JSON store that accumulates daily snapshots. Backfilled by webgia.com/chogia.vn/CoinGecko on each run.

## Key Technical Achievements
- **Robust Scraping:** Switched to stable APIs (DOJI, chogia.vn) instead of fragile HTML parsing.
- **Dual Number Format:** `utils.py` handles both VN (`.` thousands) and International (`,` thousands) formats.
- **Repository Pattern:** Clean abstraction for data sources.
- **Graceful Degradation:** Fallback mechanisms ensure the dashboard remains functional even if scraping fails.
- **Tiered Gold History:** webgia.com (1Y real SJC) → chogia.vn (30d fallback) → local store (3Y seeded from news). All scraped data backfills the local store for long-term accumulation.
- **Historical Badges:** Dashboard shows 1W/1M/1Y/3Y % change badges for all 4 assets with color-coded positive/negative/N/A styling.
- **Firebase Deployment:** Live at https://gold-dashboard-2026.web.app

## Recent Changes (Feb 2026)
- **Project reorganized:** Moved to standard Python `src` layout with `pyproject.toml`.
- **GitHub Actions workflow fixed:** Resolved merge conflict markers in `stock_repo.py` from stale worktree merge. Workflow now runs successfully on cron schedule.
- **Gold scraper fix:** Added DOJI API as primary source. SJC/Mi Hồng were broken (JS-rendered pages). DOJI returns XML with real-time SJC prices.
- **USD black market fix:** Added chogia.vn AJAX as primary source. EGCurrency was returning official bank rates (~25k) instead of true black market rates (~26k).
- **Config:** Added `DOJI_API_URL`, `CHOGIA_AJAX_URL`, `WEBGIA_GOLD_1Y_URL` to `config.py`.
- **Gold history (Phase 6):**
  - Replaced unreliable XAUT world gold proxy with real SJC data.
  - Added webgia.com scraper — parses inline Highcharts JS from 1-year SJC chart page (~282 data points).
  - chogia.vn AJAX as fallback for recent 30 days.
  - Seeded `_SJC_HISTORICAL_SEEDS` with 7 verified prices (2023–2025) from VnExpress/Tuoi Tre for immediate 3Y data.
  - All scraped data backfills `.cache/history.json` on every run.
  - Gold now shows: 1W +4.32%, 1M +11.73%, 1Y +95.04%, 3Y +170.96%.
- **Firebase caching fix:** Reduced CSS/JS cache TTL from 24h to 5min. Added `?v=2` cache-busting to asset references in `index.html`.
- **Frontend:** Updated `updateHistoryBadges` in `app.js` with N/A styling and accumulation hints. Added `.badge-na` and `.history-hint` CSS.
- **Tests:** 25/25 passing. Gold tests cover webgia success, chogia fallback, and local store fallback. USD/VND and Bitcoin tests cover seed population, backfill persistence, and wiring.
- **Deployed:** Firebase hosting at https://gold-dashboard-2026.web.app with all historical data live.

- **USD/VND history fill (Feb 2026):**
  - Added `_USD_VND_HISTORICAL_SEEDS` with 8 verified black-market rates (2023–2025) from VnExpress/CafeF/Tuoi Tre.
  - Added `_seed_historical_usd_vnd()` and `_backfill_usd_vnd_history()` methods.
  - chogia.vn data now backfills local store on every run for long-term accumulation.
- **Bitcoin history fill (Feb 2026):**
  - Added `_BTC_VND_HISTORICAL_SEEDS` with 10 verified BTC/VND prices (2022–2025) from Investopedia/CoinGecko.
  - Added `_seed_historical_bitcoin()` and `_backfill_bitcoin_history()` methods.
  - CoinGecko data now backfills local store on every run for long-term accumulation.

- **Dark Fintech UI Redesign (Feb 11 2026):**
  - Full dark theme (`#0d1117` bg, glassmorphic cards, green/red accents).
  - Layout: 2 compact metric cards (Gold + USD/VND) top row, 2 chart cards (Bitcoin + VN30) below.
  - Chart.js line charts with green gradient fill, period selectors (1W/1M/1Y/3Y).
  - Backend: `HistoryRepository.fetch_timeseries()` exposes raw `[date, value]` arrays in `data.json`.
  - `generate_data.py` now outputs `timeseries` key (295 gold, 69 USD/VND, 405 BTC, 754 VN30 points).
  - Cache-busting bumped to `?v=3` on CSS/JS references.
  - 25/25 tests still passing.

- **Frontend Bug Fixes (Feb 12 2026):**
  - Fixed footer text: "every 10 minutes" → "every 30 minutes" to match actual GH Actions cron.
  - Fixed JS `REFRESH_INTERVAL` from 10 min → 30 min (was re-fetching stale `data.json` unnecessarily).
  - Fixed `FRESHNESS_THRESHOLDS` from `{fresh: 5min, stale: 10min}` → `{fresh: 35min, stale: 65min}` so card borders no longer perpetually show "old" (red).
  - Fixed arrow direction: BTC/VN30 percentage change now shows `↘` for negative and `↗` for positive (was hardcoded `↗`).
  - Fixed missing `className` assignment in `updateVn30Card` — VN30 percentage text now correctly colored green/red.
  - Fixed period selector: clicking 1W/1M/1Y/3Y on BTC/VN30 charts now updates both the chart AND the percentage change text (was only updating chart).
  - Unified timestamps: removed per-card footer timestamps, keeping only the single header "Updated HH:MM:SS" timestamp for consistency.
  - Cleaned up dead code: removed unused `formatTimestamp()` function and `.timestamp` CSS rule.

## Next Steps
1. (Optional) Add buy/sell spread display for USD black market (chogia.vn provides both `gia_mua` and `gia_ban`).
2. (Optional) Refine Bitcoin scraper for more reliable VND conversion.
3. Deploy latest fixes to Firebase.
