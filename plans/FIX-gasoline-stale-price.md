# FIX: Gasoline price not reflecting latest VN prices

**Date:** 2026-03-25
**Reporter:** tung099077 (Discord)
**Live site:** https://gold-dashboard-2026.web.app/

---

## What the user sees

- Gasoline card shows **RON 95-III: 25.570 VND/liter**, source "Petrolimex (seed)"
- 1W and 1M history badges show **+13,64%** — clearly wrong (government-regulated prices don't jump 13% in a week)
- 1D shows +0,00% — accidentally correct (yesterday's CI snapshot was also 25570)
- The timestamp on the seed data is 2026-03-01, so the displayed price is at least 3+ weeks stale

---

## Root Cause Analysis

### RC-1: Scrapers failing in GitHub Actions (primary cause)

Both upstream sources fail when run from a US-based server:

- `xangdau.net` — likely geo-restricts or requires cookies/JS rendering
- `petrolimex.com.vn` — officially documented as potentially geo-blocked outside VN

The fallback chain in `gasoline_repo.py::fetch()` exhausts steps 1 and 2, then:
- Step 3 (`data/last_gasoline_scrape.json`) is **never persisted** between CI runs because the file lives outside the repo and is not committed
- Step 4 returns the hardcoded `_GASOLINE_SEED` (RON95=25570, timestamp=2026-03-01)

Result: every CI run has used seed data since scraping broke.

### RC-2: `_GASOLINE_SEED` vs `_GASOLINE_HISTORICAL_SEEDS` inconsistency (history bug)

| Location | Date | RON 95-III value |
|---|---|---|
| `gasoline_repo.py._GASOLINE_SEED` | 2026-03-01 | **25,570** VND |
| `history_repo.py._GASOLINE_HISTORICAL_SEEDS` last entry | 2026-03-01 | **22,500** VND |

These contradict each other. When `_gasoline_changes()` computes 1W/1M history, it looks up the old value from `_GASOLINE_HISTORICAL_SEEDS` → gets 22,500, then compares against current 25,570 → shows false +13.64%.

### RC-3: Historical seeds missing 2026 price adjustments

`_GASOLINE_HISTORICAL_SEEDS` ends at `("2026-03-01", Decimal("22500"))`.
VN prices adjust on the 1st, 11th, and 21st of each month. Since 2026-03-01, two adjustments are unrecorded:
- **2026-03-11** — price adjustment day (value unknown without live scrape)
- **2026-03-21** — price adjustment day (value unknown without live scrape)

Without these entries, the 1W and 1M comparisons always fall back to March 1 prices.

### RC-4: Seed value correctness unclear

The `_GASOLINE_SEED` value of 25,570 VND for RON 95-III may itself be stale or wrong. If the actual price changed on 2026-03-11 or 2026-03-21, the card is displaying a price that is no longer correct.

---

## Fix Plan

### Step 1 — Diagnose actual scraping failure

Run the scraper locally (from Windows machine, which is in VN or VPN-accessible):

```bash
cd gold-dashboard-arena
python - <<'PY'
from src.gold_dashboard.repositories.gasoline_repo import GasolineRepository
r = GasolineRepository()
try:
    p = r._fetch_from_xangdau()
    print("xangdau OK:", p)
except Exception as e:
    print("xangdau FAIL:", e)
try:
    p = r._fetch_from_petrolimex()
    print("petrolimex OK:", p)
except Exception as e:
    print("petrolimex FAIL:", e)
PY
```

**Expected outcomes:**
- If xangdau.net works locally but not in CI → geo-block; need a CI-accessible source
- If regex match fails → HTML structure changed; update `_extract_grade_price` search window or pattern
- If HTTP 403/timeout → need different headers or source

### Step 2 — Verify current actual VN gasoline prices

Manually check the current official price from one of:
- `https://xangdau.net/` (in browser)
- `https://www.petrolimex.com.vn/nd/gia-ban-le-xang-dau.html` (in browser)
- `https://pvoil.com.vn/` (PV Oil, another major state retailer)

Record:
- Current RON 95-III price (VND/liter)
- Current E5 RON 92 price (VND/liter)
- Date of last official adjustment (1st, 11th, or 21st)
- Price on the previous adjustment date (for 2026-03-11 and/or 2026-03-21)

### Step 3 — Add a CI-accessible fallback scraper source

If both current sources fail in GitHub Actions, add a third fallback using a source accessible internationally. Options:

**Option A — pvoil.com.vn** (PV Oil official site):
- Scrape `https://pvoil.com.vn/` for retail price table
- Similar HTML scraping approach as petrolimex

**Option B — Vietnamese government open data** (if available):
- MOIT (Bộ Công Thương) occasionally publishes price adjustment notices

**Option C — Hardcode price after each official adjustment**:
- Since prices only change ~3× per month on a fixed schedule, manually update `_GASOLINE_SEED` and `_GASOLINE_HISTORICAL_SEEDS` after each official MOIT announcement
- Less maintenance burden than a failing scraper

**Recommended:** Implement Option A (pvoil.com.vn) as step 3 in the fallback chain, before the seed. Add it in `gasoline_repo.py::fetch()` between steps 2 and 3.

### Step 4 — Fix `_GASOLINE_HISTORICAL_SEEDS` inconsistency

**File:** `src/gold_dashboard/repositories/history_repo.py`

The last entry `("2026-03-01", Decimal("22500"))` contradicts the current seed price of 25570. This needs to be corrected once actual prices are verified in Step 2.

Actions:
1. Determine what the actual RON 95-III price was on 2026-03-01
2. If it was ~22500, update `_GASOLINE_SEED` in `gasoline_repo.py` to 22500 (the seed was wrong)
3. If it was ~25570, update `_GASOLINE_HISTORICAL_SEEDS` 2026-03-01 entry to 25570 (the historical seed was wrong)
4. Add entries for 2026-03-11 and 2026-03-21 with verified prices
5. Ensure at least monthly density of entries from 2026-01-01 onward so the ±3-day tolerance in `get_value_at()` always resolves 1D/1W/1M lookups

Example additions (fill in actual values after Step 2):
```python
# --- 2026 ---
("2026-01-01", Decimal("XXXXX")),
("2026-01-11", Decimal("XXXXX")),
("2026-01-21", Decimal("XXXXX")),
("2026-02-01", Decimal("XXXXX")),
("2026-02-11", Decimal("XXXXX")),
("2026-02-21", Decimal("XXXXX")),
("2026-03-01", Decimal("XXXXX")),
("2026-03-11", Decimal("XXXXX")),  # add after Step 2
("2026-03-21", Decimal("XXXXX")),  # add after Step 2
```

### Step 5 — Update `_GASOLINE_SEED` and fallback constants

**Files:** `src/gold_dashboard/repositories/gasoline_repo.py`, `src/gold_dashboard/config.py`

After confirming actual current prices:
1. Update `_GASOLINE_SEED` in `gasoline_repo.py` to the current verified price with today's date
2. Update `GASOLINE_FALLBACK_RON95_PRICE` and `GASOLINE_FALLBACK_E5_RON92_PRICE` in `config.py` to match

### Step 6 — Run generate_data.py locally and verify

```bash
cd gold-dashboard-arena
python -m gold_dashboard.generate_data
```

Check `public/data.json`:
- `gasoline.ron95_price` reflects the correct current price
- `gasoline.source` is NOT "Petrolimex (seed)" — it should show "xangdau.net" or "pvoil.com.vn"
- `history.gasoline` 1D/1W/1M show small, plausible deltas (not 13.64%)

### Step 7 — Deploy

```bash
git add src/gold_dashboard/repositories/gasoline_repo.py
git add src/gold_dashboard/repositories/history_repo.py
git add src/gold_dashboard/config.py
git add public/data.json
git commit -m "fix(gasoline): fix stale seed, update historical seeds, add pvoil fallback"
git push
```

GitHub Actions will redeploy to Firebase on push.

---

## Files to modify

| File | Change |
|---|---|
| `src/gold_dashboard/repositories/gasoline_repo.py` | Add pvoil.com.vn as step 3 fallback; update `_GASOLINE_SEED` to current verified price |
| `src/gold_dashboard/repositories/history_repo.py` | Fix `_GASOLINE_HISTORICAL_SEEDS`: correct 2026-03-01 value; add 2026-03-11, 2026-03-21 entries |
| `src/gold_dashboard/config.py` | Update `GASOLINE_FALLBACK_RON95_PRICE`, `GASOLINE_FALLBACK_E5_RON92_PRICE`, add `PVOIL_URL` |
| `public/data.json` | Regenerate after fixes |

---

## Acceptance Criteria

- [ ] Gasoline card shows source other than "Petrolimex (seed)"
- [ ] RON 95-III price matches the current official VN retail price
- [ ] 1D history badge shows a delta of 0% or a small realistic change (not 13.64%)
- [ ] 1W and 1M badges show plausible changes consistent with VN price schedule
- [ ] `generate_data.py` runs cleanly in CI (GitHub Actions) without falling back to seed
