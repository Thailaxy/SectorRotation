# US Sector & Theme Rotation Tracker

แดชบอร์ดสำหรับติดตามการหมุนเวียนของเงินทุนในตลาดหุ้นสหรัฐ (Sector & Theme Rotation) ผ่านกราฟ Relative Rotation Graph (RRG) และ Heatmap แบบรายวัน 

เครื่องมือนี้คำนวณข้อมูลแบบ **Equal-weight** เป็นหลัก เพื่อดูทิศทางของ "กลุ่ม" โดยไม่ถูกบิดเบือนจากหุ้นยักษ์ใหญ่เพียงไม่กี่ตัว 

> **คำเตือน:** ข้อมูลบนหน้านี้เป็นเครื่องมือเพื่อการศึกษาและสังเกตการณ์เท่านั้น ไม่ใช่คำแนะนำการลงทุนหรือคำแนะนำซื้อขายรายตัว

## วิธีติดตั้งและรันบนเครื่องตัวเอง (Local Development)

โปรเจกต์นี้ถูกออกแบบมาให้เรียบง่ายที่สุดโดยไม่ต้องใช้ Database หรือ Backend server ซับซ้อน การคำนวณทั้งหมดทำผ่าน Python script และได้ผลลัพธ์เป็นไฟล์ `data.json` เดี่ยวๆ สำหรับให้เว็บ (HTML/CSS/JS) นำไปแสดงผล

### สิ่งที่ต้องมี
- Python 3.11 หรือใหม่กว่า
- Git

### ขั้นตอนการรัน

1. **โคลนโปรเจกต์ลงมาที่เครื่อง:**
   ```bash
   git clone <repo-url>
   cd Rotation
   ```

2. **สร้างและเปิดใช้งาน Virtual Environment:**
   ```bash
   # สำหรับ Mac/Linux:
   python -m venv .venv
   source .venv/bin/activate

   # สำหรับ Windows:
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. **ติดตั้ง Library ที่จำเป็น:**
   ```bash
   pip install -r requirements.txt
   ```

4. **ดึงข้อมูลราคาและคำนวณผลลัพธ์:**
   ```bash
   python -m pipeline.run
   ```
   *คำสั่งนี้จะไปดึงราคาหุ้นย้อนหลังจาก Yahoo Finance แล้วคำนวณค่าต่างๆ (RRG, ผลตอบแทน, Breadth) จากนั้นบันทึกผลลงในโฟลเดอร์ `web/public/data.json`*

5. **เปิดหน้าเว็บเพื่อดูผลลัพธ์:**
   ```bash
   cd web/public
   python -m http.server 8000
   ```
   *เปิดเบราว์เซอร์แล้วเข้าไปที่ `http://localhost:8000`*

### การรัน Unit Test
เพื่อตรวจสอบความถูกต้องของสูตรคำนวณ สามารถรันคำสั่ง:
```bash
pytest
```

## สถาปัตยกรรม (Architecture)
โปรเจกต์นี้ใช้ GitHub Actions ในการดึงข้อมูลและอัปเดตไฟล์ `data.json` โดยอัตโนมัติทุกวันหลังตลาดสหรัฐปิดทำการ และใช้ GitHub Pages ในการโฮสต์หน้าเว็บ ทำให้ไม่มีค่าใช้จ่ายในการดูแลระบบ (100% Free)

## Handoff Log

### 2026-07-04 — Fix Yahoo fetch on GitHub Actions, fix empty RRG, add light theme, plan ticker audit

**Goal:** Data pipeline couldn't fetch from Yahoo Finance when run in GitHub Actions (worked
locally, empty in CI), forcing manual prices.csv uploads. Fix the automated fetch, then address
follow-on issues found while verifying the fix.

**Changes:**
- `pipeline/fetch.py` — replaced a plain `requests.Session` + fake User-Agent with an explicit
  `curl_cffi.requests.Session(impersonate="chrome")`. The plain session had disabled yfinance's
  built-in curl_cffi TLS-impersonation auto-detection, which is what Yahoo's bot detection
  actually checks for on datacenter IPs (GitHub Actions runners). Also added per-attempt
  `df.shape`/error logging so future failures are diagnosable from the Actions log.
- `requirements.txt` — added `curl_cffi`.
- `config.yaml` — `history_days: 400 -> 850`. `pipeline/metrics.py::calc_rrg()` z-scores
  RS-Ratio over a rolling 52-week window, then z-scores RS-Momentum (diff of RS-Ratio) over
  *another* rolling 52-week window on top of that — needs ~2x the lookback to produce even one
  point. 400 days (~57 weeks) was nowhere near enough, so `rrg` was `null` for every theme and
  the RRG chart / Momentum Playbook stayed empty despite the fetch itself working.
- `web/public/theme.js` (new) — light/dark theme toggle, same localStorage pattern as the
  existing EN/TH toggle (`i18n.js`).
- `web/public/styles.css` — added `html[data-theme="light"]` CSS variable overrides.
- `web/public/index.html` — added theme toggle button + inline head script to set
  `data-theme` from localStorage before first paint (avoids flash of wrong theme).
- `web/public/app.js` — RRG chart's axis label / gridline / quadrant colors were hardcoded hex
  values; changed to read from CSS custom properties at render time (`getCssVar`/`getColorMap`)
  so the chart actually follows the active theme instead of staying dark-only.
- `TICKER_AUDIT_PLAN.md` (new) — read-only verification plan for a separate AI/session to audit
  `data/universe.yaml`'s ~89 tickers for delistings/renames/symbol-reassignment risk. Written,
  not yet executed.

**What worked:**
- curl_cffi fix confirmed live: triggered `workflow_dispatch`, Actions run completed with
  `warnings: []` and real non-null returns/breadth/volume for all 36 themes (previously all
  null). Cache CSVs (`cache/prices.csv`, `cache/volumes.csv`) now refresh with real data too.
- `history_days` fix confirmed via synthetic data before pushing: fed `calc_rrg()` fabricated
  price series at 400/700/780/800/900/1000 days — 400 and 700 returned `None`, 780+ returned a
  full 8-week tail. After deploy, pulled the actual `data.json` and confirmed 0/36 themes have
  `rrg: null` (was 36/36 null before).
- Light theme verified end-to-end with a real headless-Chromium run (installed Playwright +
  Chromium locally since `chromium-cli` wasn't available): default dark theme confirmed, click
  on `#themeToggle` switches to light bg/dark text, RRG chart colors follow, choice persists in
  `localStorage` across reload, zero console errors. Screenshots reviewed visually — both
  themes readable, chart quadrant tints and badges look correct in both.
- `tests/` suite (5 tests) still passes after all changes.

**Mistakes & recovery:**
- A prior session's fix (before this one) had already tried a plain `requests.Session` + fake
  User-Agent and it didn't actually fix anything — root cause wasn't diagnosed at the time, just
  worked around blindly. This session found the real reason (session override disables
  yfinance's own curl_cffi detection) before applying a different fix.
- Local Python is 3.14 with no Python 3.11 available, and `pandas==2.2.2` (pinned in
  requirements.txt for CI) has no prebuilt wheel for 3.14 — couldn't install requirements.txt
  verbatim into a local venv. Worked around by installing unpinned equivalents just for a local
  smoke test, without touching the pinned versions CI actually uses.
- This machine's corporate network intercepts/blocks outbound TLS to Yahoo entirely (confirmed:
  even plain `requests` gets the identical `CERTIFICATE_VERIFY_FAILED` error as curl_cffi) — so
  the real fetch fix could only be verified by pushing and checking the actual GitHub Actions
  run, not locally.
- While smoke-testing `fetch_data()` locally with only `['NVDA','AMD']`, the function's
  unconditional `to_csv(cache_file)` overwrote the full ~130-ticker `cache/prices.csv` /
  `volumes.csv` with just 3 columns. Caught via `git diff --stat` before committing anything;
  reverted with `git checkout -- cache/prices.csv cache/volumes.csv` before proceeding.
- First deploy after the curl_cffi fix still showed an empty RRG chart in the browser — took a
  round of investigation to separate two different empty-RRG causes: (1) confirmed via
  `data.json` that the *first* deploy had a real second bug (`history_days` too short — see
  above); (2) after fixing that and redeploying, user reported still seeing an empty chart,
  which was diagnosed as likely browser/GitHub-Pages CDN caching (`Cache-Control: max-age=600`)
  rather than a data problem, since the pulled `data.json` at that point was already fully
  populated (`rrg` non-null for all 36 themes). User was advised to hard-refresh; **this was not
  explicitly re-confirmed by the user before the session moved on to other tasks** — see open
  items below.

**Open TODOs / blockers:**
- [ ] Not yet confirmed: does the RRG chart / Momentum Playbook actually render correctly in the
      user's browser after a hard refresh? Backend data (`data.json`) is confirmed correct as of
      commit `6e79e26`; the caching theory was never explicitly verified against the live page.
- [ ] `TICKER_AUDIT_PLAN.md` has not been executed yet — need another AI/session to run it and
      produce `TICKER_AUDIT_REPORT.md`, then a human decides what to apply to
      `data/universe.yaml`.
- [ ] Repo root still has leftover one-off debug scripts from earlier troubleshooting
      (`debug_dummy.py`, `debug2.py`, `debug_yf_threads.py`, `test_fetch.py`, `test_fetch_2.py`,
      `output.log`, `output2.log`, stray `.jpg`/`.webp` images) — flagged as optional cleanup,
      not yet done.
- [ ] Light theme changes (`theme.js`, `index.html`, `styles.css`, `app.js`) and
      `TICKER_AUDIT_PLAN.md` are uncommitted as of this handoff entry — commit + push planned as
      part of this same handoff.

**Repro / verify:**
```bash
# unit tests
pytest tests/

# local dashboard preview (no network fetch needed, uses committed data.json)
cd web/public && python -m http.server 8000
# open http://localhost:8000, click the moon/sun button next to EN/TH to test theme toggle

# full pipeline run (needs unrestricted network access to Yahoo Finance — will fail on networks
# that block/intercept it, e.g. this dev machine; works in GitHub Actions)
python -m pipeline.run
```

**Commits today:** `b9f2ff7` `12390fa` (plus this handoff commit and the pending light-theme /
audit-plan commit)
