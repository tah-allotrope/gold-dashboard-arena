# Active Context

## Project Snapshot
- **Project:** Vietnam Gold Dashboard (Firebase Hosting)
- **Goal:** Scrape Vietnamese gold price (SJC/local) alongside USD/VND (black market), Bitcoin, and VN30 index; render via web dashboard.
- **Status:** Phase 10 Complete - Cyberpunk neon theme, VN30 chart fix, land fallback hardening, deployed (Feb 28, 2026).
- **Cadence:** 30-minute refresh (GitHub Actions cron `*/30`).

## Current Files
- **Web Dashboard (Firebase):**
  - `public/index.html` - Responsive web dashboard with Vietnamese number formatting.
  - `public/styles.css` - Cyberpunk neon theme with responsive layout.
  - `public/app.js` - Frontend data fetching, rendering, and neon chart styling.
  - `public/data.json` - Generated market data (auto-generated).
  - `firebase.json` - Firebase hosting configuration.
  - `.firebaserc` - Firebase project settings.
- **Terminal Dashboard (Legacy):** `src/gold_dashboard/main.py`, `src/gold_dashboard/dashboard.py` (Rich UI).
- **Data Layer:** 
  - `src/gold_dashboard/models.py` - Dataclasses for market data.
  - `src/gold_dashboard/utils.py` - Sanitization and caching logic.
  - `src/gold_dashboard/repositories/` - Data fetching logic for Gold, Currency, Crypto, Stocks, and Land.
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
- **Historical Badges:** Dashboard shows 1D/1W/1M/1Y/3Y % change badges for all 5 assets with color-coded positive/negative/N/A styling.
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
  - GitHub Actions follow-up (same day):
    - Observed one CI failure where VN30 temporary fallback status (`Fallback (Scraping Failed)`) marked payload as severe and blocked deploy.
    - Tuned severity policy in `generate_data.py`: VN30 fallback/short-timeseries remain `degraded` reasons, but no longer set `health.severe_degradation=true` by themselves.
    - Kept severe failures strict for truly critical payload breakage (e.g., missing required current sections).
    - Updated regression expectation in `tests/test_generate_data.py` and re-ran targeted suite: **35/35 passing**.
    - Noted operational constraint: `public/data.json` is gitignored, so CI cannot rely on repo-committed LKG unless a separate persistence strategy is introduced.

- **Land First-Class Asset Correction (Feb 16 2026):**
  - Replaced benchmark-only payload path with a required top-level **`land`** asset block in `generate_data.py` (`price_per_m2`, `location`, `unit`, `source`, `timestamp`).
  - Added dedicated `LandPrice` model and `LandRepository`:
    - `src/gold_dashboard/models.py` now includes `LandPrice` and `DashboardData.land`.
    - `src/gold_dashboard/repositories/land_repo.py` scrapes Hong Bang-related listings from `alonhadat.com.vn` and derives `VND/m2` via parsed `(price, area)` pairs.
    - Fallback remains resilient via `LAND_FALLBACK_PRICE_PER_M2` to keep payload generation stable.
  - Extended data pipelines for parity with other assets:
    - Land fetch + snapshot recording in both `generate_data.py` and `main.py`.
    - Land history/timeseries support in `history_repo.py` with seed anchors and local-store accumulation.
    - Health policy updated so missing/invalid land section is treated as severe degradation.
    - CI payload gate now requires `land` in `.github/workflows/update-dashboard.yml`.
  - Updated web UI to Land metric-card pattern (not benchmark panel):
    - `public/index.html`: adds `#landCard` with 1D/1W/1M/1Y/3Y badges.
    - `public/app.js`: `updateLandCard`/`resetLandCard`, land history badge wiring.
    - `public/styles.css`: top row adjusted for 3 metric cards; removed legacy benchmark styles.
    - Cache-busting bumped to `styles.css?v=7` and `app.js?v=8`.
  - Added/updated tests:
    - `tests/test_generate_data.py`: land serialization, merge-current timeseries, and health severity checks.
    - `tests/test_history.py`: land included in required history assets + land seed tests.
    - `tests/test_land_repo.py`: parser extraction and fallback behavior.

- **Smokecheck + Gold 3Y Regression Fix (Feb 16 2026):**
  - Smokecheck completed end-to-end:
    - `python -m gold_dashboard.generate_data` passed with all required asset sections, including `land`.
    - Contract assertion verified `land` in current payload, `history.land`, and `timeseries.land`.
    - Local web smokecheck served via `python -m http.server` against `public/`.
  - Fixed missing Gold 3Y history value:
    - Root cause: strict local-history tolerance could miss 3Y anniversary while nearby SJC seeds existed.
    - Added 3Y seed-nearest fallback in `_gold_changes()` using `_find_seed_rate(..., max_delta_days=45)`.
    - Added regression test `test_gold_3y_uses_seed_nearest_when_local_misses` in `tests/test_history.py`.
    - Regenerated payload confirms Gold `3Y` is now populated (non-null old value and percent change).

- **Cyberpunk Neon Theme + 5-Issue Fix (Feb 28 2026):**
  - **VN30 flat line charts fixed:**
    - Removed 40 inaccurate hardcoded `_VN30_HISTORICAL_SEEDS` from `_vn30_timeseries()` in `history_repo.py`. Seeds created ±200pt spikes that compressed real VPS data into apparent flat lines. Seeds retained for `_vn30_changes()` 3Y % fallback only.
    - Replaced `filterTimeseries()` all-data dump fallback in `app.js` with progressive window expansion (2x → 4x → 90d → last 60 points). Short periods during data gaps (e.g., Tet holiday) now show the nearest available data instead of compressing 768+ points.
  - **Land fallback chain hardened (4-step):**
    - Added homedy.com as international-friendly scraper (`_fetch_from_homedy()` in `land_repo.py`). Parses pre-calculated "X tr/m2" values directly from listing cards.
    - Added `_parse_vn_number()` heuristic for Vietnamese number formatting: dot + 3 trailing digits = thousands separator, dot + 1-2 digits = decimal point. Prevents 10x price inflation on dot-decimal values.
    - Added persistence layer: `_persist_last_good_scrape()` / `_load_last_good_scrape()` using `data/last_land_scrape.json` (gitignored).
    - Hardcoded `_LAND_SEED` (183.8M from homedy.com 2026-02-28) as fallback when persisted file doesn't exist on fresh CI clones.
    - Full chain: alonhadat.com.vn → homedy.com → persisted file → seed → hardcoded 255M.
    - Config additions: `HOMEDY_HONG_BANG_URL`, `LAND_LAST_GOOD_SCRAPE_FILE` in `config.py`.
  - **History badge sizing fixed:**
    - `.period-value` increased to 0.78rem with 0.4rem/0.3rem padding; values like "+28,38%" no longer clip.
    - Hover glow border added to badges.
  - **Layout widened:**
    - Container max-width 900px → 1400px.
    - New 1100px tablet breakpoint: 2-col metrics (3rd card full-width), 1-col charts.
    - Chart min-height increased from 140px to 180px.
  - **Full cyberpunk neon theme:**
    - Color palette: neon cyan (#00f0ff), green (#39ff14), pink (#ff2d55), magenta (#ff00ff), gold (#ffcf00).
    - Orbitron font for headings and values; Inter retained for body text.
    - Glowing card borders with `::before` top-edge gradient lines.
    - Scanline overlay (`body::after` repeating-linear-gradient).
    - Neon text-shadow on values, badge text, and change indicators.
    - Chart line color switched to cyan with gradient fill; neon-styled tooltips.
    - Custom neon scrollbar (`::-webkit-scrollbar` cyan theme).
    - Freshness indicators now use inset glow shadows (green/gold/red).
  - Cache-busting bumped: `styles.css?v=8`, `app.js?v=9`. Orbitron added to Google Fonts import.
  - Verified end-to-end: `generate_data.py` produces land source "homedy.com" at 183.8M VND/m2.
  - Deployed to Firebase: https://gold-dashboard-2026.web.app

## Next Steps
1. Monitor at least 2 scheduled GitHub Actions runs to confirm stable deploys with homedy.com land fallback working from CI.
2. (Optional) Add buy/sell spread display for USD black market (chogia.vn provides both `gia_mua` and `gia_ban`).
3. (Optional) Add a lightweight frontend smoke test in CI to validate card rendering contract (`gold/usd/land` current + history badges).
4. (Optional) Add animated neon pulse or particle effects to the dashboard header.

## Active Task - Gasoline stale price fix (Mar 25 2026)
- [x] Add regression tests for stale gasoline seeds, bad 1W/1M deltas, and payload-health degradation rules.
- [x] Prevent seed/fallback gasoline values from being recorded as fresh current history snapshots.
- [x] Mark stale/seed/fallback gasoline payloads as degraded so LKG restoration can protect production output.
- [x] Align gasoline seed/history constants so short-period badges do not fabricate large moves from contradictory values.
- [x] Run targeted tests and regenerate `public/data.json` to confirm realistic gasoline source/history output.

## Review / Results
- Added gasoline regression coverage in `tests/test_history.py`, `tests/test_generate_data.py`, and `tests/test_gasoline_repo.py`.
- `generate_data.py` now treats gasoline seed/fallback/stale timestamps as degraded, skips snapshot writes for stale non-live gasoline, and refuses to restore a degraded gasoline block from an already-degraded previous payload.
- `history_repo.py` now computes gasoline short-period changes source-aware: when the current gasoline value is seed/fallback/cached, it avoids polluted local-history snapshots and falls back to curated seeds.
- `utils.py` cache deserialization now reconstructs `GasolinePrice`, fixing runtime failures when gasoline fetches come from the shared cache.
- Verified with `python -m unittest tests.test_gasoline_repo tests.test_generate_data tests.test_history` (47/47 passing) and `python -X utf8 -m gold_dashboard.generate_data`.
- Result: bogus gasoline `1W`/`1M` +13.64% badges are fixed to `0.0`, but the live current source is still the stale seed because both current scrapers still fail to parse from this environment.
