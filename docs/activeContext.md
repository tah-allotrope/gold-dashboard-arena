# Active Context

## Project Snapshot
- **Project:** Vietnam Gold Dashboard (Firebase Hosting)
- **Goal:** Scrape Vietnamese gold price (SJC/local) alongside USD/VND (black market), Bitcoin, and VN30 index; render via web dashboard.
- **Status:** Phase 9 In Progress - Reliability hardening pass implemented (Feb 15, 2026).
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

- **Data Integrity & Consistency Pass (Feb 14 2026):**
  - Enforced UTC metadata: `generated_at` now serialized as timezone-aware ISO8601 with `Z`.
  - Added `merge_current_into_timeseries()` in `generate_data.py` so same-day card values always match latest chart points.
  - Added guard to discard future-dated timeseries points before same-day upsert.
  - Fixed history lookup tolerance edge case: `history_store.get_value_at()` now compares by calendar day (not time-of-day timedeltas), preventing false `3Y` null misses.
  - Frontend header now uses payload generation time (`generated_at`) with asset timestamp fallback, instead of browser-local fetch time.
  - Frontend now explicitly resets cards to `Unavailable` when payload sections are missing, preventing stale DOM values from persisting.
  - Cache-busting bumped for JS: `app.js?v=5`.

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

- **Firebase vs Localhost Mismatch Fixes (Feb 12 2026):**
  - **Timestamp fix:** Appended `Z` (UTC marker) to all `.isoformat()` calls in `generate_data.py`. GH Actions runs in UTC but `datetime.now()` produced naive timestamps; JS interpreted them as local time → cards always showed red "old" borders. Now JS correctly parses as UTC.
  - **Gold 3Y fix:** Added SJC seed entries at `2023-01-15` and `2023-02-12` to `_SJC_HISTORICAL_SEEDS` in `history_repo.py`. The 3Y lookback was returning null because `MAX_LOOKUP_TOLERANCE_DAYS=3` uses `timedelta(days=3)` (exactly 72h) and the nearest seed (`2023-02-10`) had a delta of 3d19h — just over the limit.
  - **USD/VND 3Y fix:** Same root cause — added seed at `2023-02-13` to `_USD_VND_HISTORICAL_SEEDS`. USD/VND 3Y now shows +10.08%.
  - **USD/VND black market premium:** chogia.vn is geo-blocked from GH Actions (US/EU IPs), causing fallback to ExchangeRate API (official bank rate ~25,946 instead of black market ~26,500). Added `BLACK_MARKET_PREMIUM = 1.025` to `config.py` and applied it in `currency_repo.py` `_fetch_from_open_er_api()`. Source labeled "ExchangeRate API (est.)".
  - **Badge truncation fix:** Added `min-width: 0; white-space: nowrap;` to `.history-badge` in `styles.css` to prevent "N/A" truncating to "N" on the Gold card.
  - **Cache-busting:** Bumped `?v=3` → `?v=4` on CSS/JS references in `index.html`.
  - 25/25 tests still passing.

- **Production Sync & Validation (Feb 14 2026):**
  - Added regression tests in `tests/test_generate_data.py` for:
    - UTC `generated_at` with `Z` suffix.
    - Current snapshot vs latest timeseries reconciliation.
    - Future-point discard behavior.
  - Added regression test in `tests/test_history.py` for calendar-day tolerance near the 3-day boundary.
  - Targeted suite now passing: **30/30** (`python -m unittest tests.test_generate_data tests.test_history`).
  - Fresh `public/data.json` generated and sanity-checked: all 4 assets have same-day current values matching latest timeseries points.
  - Committed release: `e50bbcb`.
  - Deployed successfully to Firebase Hosting (`gold-dashboard-2026`): https://gold-dashboard-2026.web.app

- **Reliability Hardening (Feb 15 2026):**
  - Added payload health assessment in `generate_data.py` with per-asset status/reasons and `health.severe_degradation` flag.
  - Added last-known-good (LKG) restoration in `generate_data.py`: when a run is severely degraded, affected asset blocks (`current + history + timeseries`) are restored from previous `public/data.json` before writing output.
  - Hardened VN30 current fetch chain in `stock_repo.py`:
    - Added VPS retries/backoff helper (`_fetch_vps_closes`).
    - Added `VPS (last close)` fallback path over a wider window before CafeF/static fallback.
    - Kept hardcoded static VN30 value as absolute final fallback only.
  - Reduced USD/VND historical null risk in `history_repo.py`:
    - Added exact 1Y seed anchor (`2025-02-14`) to `_USD_VND_HISTORICAL_SEEDS`.
    - Added nearest-seed fallback (`_find_seed_rate`) when chogia/local store lookup misses rolling target dates.
  - Added CI payload quality gate in `.github/workflows/update-dashboard.yml`:
    - Fails run if any required asset section is missing.
    - Fails run if payload reports `health.severe_degradation = true`.
  - Added regression tests:
    - `tests/test_stock_repo.py` for VN30 fallback-order behavior.
    - New health/LKG tests in `tests/test_generate_data.py`.
    - Seed-nearest USD fallback test in `tests/test_history.py`.
  - Targeted reliability suite now passing: **35/35** (`python -m unittest tests.test_generate_data tests.test_history tests.test_stock_repo`).

## Next Steps
1. Push reliability hardening commit(s) to remote and monitor at least 2 cron cycles for stable `health.overall=ok` payloads.
2. Verify production `public/data.json` no longer degrades VN30 to static fallback when VPS last-close data is available.
3. (Optional) Add buy/sell spread display for USD black market (chogia.vn provides both `gia_mua` and `gia_ban`).
4. (Optional) Add a lightweight frontend smoke test to assert degraded-payload/LKG restoration behavior in CI.
