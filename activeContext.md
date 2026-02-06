# Active Context

## Project Snapshot
- **Project:** Vietnam Gold Dashboard (Firebase Hosting)
- **Goal:** Scrape Vietnamese gold price (SJC/local) alongside USD/VND (black market), Bitcoin, and VN30 index; render via web dashboard.
- **Status:** Phase 5 Complete - Scrapers fixed and deployed to Firebase.
- **Cadence:** 10-minute refresh (per user directive).

## Current Files
- **Web Dashboard (Firebase):**
  - `public/index.html` - Responsive web dashboard with Vietnamese number formatting.
  - `public/styles.css` - Modern, mobile-friendly styling.
  - `public/app.js` - Frontend data fetching and rendering.
  - `public/data.json` - Generated market data (auto-generated).
  - `generate_data.py` - Data generation script for static export.
  - `firebase.json` - Firebase hosting configuration.
  - `.firebaserc` - Firebase project settings.
- **Terminal Dashboard (Legacy):** `main.py`, `dashboard.py` (Rich UI).
- **Data Layer:** 
  - `models.py` - Dataclasses for market data.
  - `utils.py` - Sanitization and caching logic.
  - `repositories/` - Data fetching logic for Gold, Currency, Crypto, and Stocks.
- **Docs:** `AGENTS.md`, `research.md`, `activeContext.md`, `README_DEPLOYMENT.md`.

## Implementation Status
- **VN30 Index (Vietstock):** Working. Extracts value and change percentage.
- **Gold (DOJI API):** Working. SJC retail prices via DOJI XML API (primary).
- **USD/VND (chogia.vn):** Working. Black market rates via AJAX JSON (primary).
- **Bitcoin (CoinMarketCap):** Fallback Mode. Complex DOM structure. Fallback to conversion rates.

## Key Technical Achievements
- **Robust Scraping:** Switched to stable APIs (DOJI, chogia.vn) instead of fragile HTML parsing.
- **Dual Number Format:** `utils.py` handles both VN (`.` thousands) and International (`,` thousands) formats.
- **Repository Pattern:** Clean abstraction for data sources.
- **Graceful Degradation:** Fallback mechanisms ensure the dashboard remains functional even if scraping fails.
- **Firebase Deployment:** Live at https://gold-dashboard-2026.web.app

## Recent Changes (Feb 2026)
- **Gold scraper fix:** Added DOJI API as primary source. SJC/Mi Hồng were broken (JS-rendered pages). DOJI returns XML with real-time SJC prices.
- **USD black market fix:** Added chogia.vn AJAX as primary source. EGCurrency was returning official bank rates (~25k) instead of true black market rates (~26k).
- **Config:** Added `DOJI_API_URL` and `CHOGIA_AJAX_URL` to `config.py`.
- **Deployed:** Firebase hosting at https://gold-dashboard-2026.web.app with corrected data.

## Next Steps
1. (Optional) Automate `generate_data.py` execution via GitHub Actions or local Task Scheduler for periodic data refresh.
2. (Optional) Refine Bitcoin scraper. 
3. (Optional) Add buy/sell spread display for USD black market (chogia.vn provides both `gia_mua` and `gia_ban`).
