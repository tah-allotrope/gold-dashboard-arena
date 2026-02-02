# Active Context

## Project Snapshot
- **Project:** Vietnam Gold Dashboard
- **Goal:** Scrape Vietnamese gold price (SJC/local) alongside USD/VND (black market), Bitcoin, and VN30 index; render via `rich` dashboard.
- **Cadence:** 10-minute refresh.
- **Status:** Improved scraping and stability.

## Architecture Decision
**Use Python Dataclasses for Models:** Replaced Pydantic v2 with Python dataclasses to avoid Rust compilation requirements that cause issues on Python 3.14+. Dataclasses provide sufficient validation via `__post_init__` without external binary dependencies.

## Source Status
1. **Gold (Local):** Added `24h.com.vn` as a reliable HTML source. SJC and Mi Hồng remain as fallbacks.
2. **USD/VND (Black Market):** `EGCurrency` working (requires `brotli` for decoding).
3. **VN30 Index:** `Vietstock` working.
4. **Bitcoin:** `CoinMarketCap` working.

## Constraints & Standards
- Use `requests` with strict headers.
- Use `Decimal` for financial data.
- Handle dual number formats (VN and International).
- Cache for 10 minutes with stale-data fallback.
- No binary files or local cache files in repository.
