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
โปรเจกต์นี้ใช้ GitHub Actions ในการดึงข้อมูลและอัปเดตไฟล์ `data.json` โดยอัตโนมัติทุกวันหลังตลาดสหรัฐปิดทำการ และใช้ **Firebase Hosting** ในการโฮสต์หน้าเว็บ ทำให้ไม่มีค่าใช้จ่ายในการดูแลระบบ (100% Free บน Firebase Spark plan)

- **Live URL:** https://sectorrotation-wk.web.app
  - (เดิมใช้ `sectorrotation-546e0.web.app` ระหว่าง migrate — ตอนนี้ deploy ไปที่ site `sectorrotation-wk` ในโปรเจกต์เดียวกันผ่าน multisite target)
- **Deploy workflow ทั้งสองตัว:**
  - `.github/workflows/daily.yml` — รัน pipeline + commit data + deploy ทุกวันทำการ 22:30 UTC
  - `.github/workflows/deploy-site.yml` — deploy เฉพาะ frontend เมื่อมี push ไปยัง `main`

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

### 2026-07-04 (cont.) — Dividend-adjusted returns fix, theme/badge contrast fixes, sortable Zone column, deploy-on-push gap found and fixed

**Goal:** Continue from the earlier entry today: user spotted our 1M returns didn't match
Yahoo Finance's displayed % for sector ETFs (XLI, XLE), then flagged the light theme making the
page title unreadable and a column-hover bug, then asked for a more "production grade" table
for investor review, then reported the fix "didn't show up" on the live site, then asked for
the new Theme/Zone columns to be sortable too.

**Changes:**
- `pipeline/fetch.py`, `spec.md` — switched `yf.download(..., auto_adjust=True)` to
  `auto_adjust=False` + plain `Close` column. Root cause of the Yahoo mismatch: `auto_adjust=True`
  bakes dividend adjustments into historical prices (total return), so our 1M/3M etc. included
  dividends paid during the window while Yahoo's basic price chart doesn't. Traced XLE's exact
  gap (-7.52% ours vs -8.18% Yahoo) to its ~June 19 ex-dividend date sitting inside that specific
  1-month window, confirmed by a visible boundary in `cache/prices.csv` between long-decimal
  "adjusted" values before it and clean 2-decimal raw values after. User chose price-only to
  match Yahoo's chart, so `spec.md` (§8.3, §16) updated too since it explicitly called for
  `auto_adjust=True` before.
- `.github/workflows/deploy-site.yml` (new) — `daily.yml` only triggers on `schedule`/
  `workflow_dispatch`, never `push`, so frontend-only commits were being pushed but never
  actually deployed; the live site kept serving whatever the last cron/manual run had built.
  Added a separate lightweight workflow that just re-uploads and redeploys the current
  `web/public` on every push to `main`, without touching the data pipeline (no new commits
  created, so no loop risk with the daily bot's own data commits).
- `web/public/styles.css`, `app.js` — fixed two reported bugs (page title hardcoded to the dark
  theme's text color, unreadable in light mode at 1.11:1 contrast; sortable column header hover
  turned text white, invisible on the light theme's white panel). While fixing those, ran actual
  WCAG contrast numbers (dataviz skill's validator) on every quadrant badge color instead of
  eyeballing, and found pre-existing failures beyond what was reported — e.g. white text on the
  dark-theme "Leading" badge measured 2.28:1, badly under the 3:1 floor. Replaced guessed
  white/black badge text with per-status, per-theme `--*-text` tokens chosen from the real
  numbers. Also fixed heatmap return cells: hardcoded to the dark theme's raw green/red rgb()
  regardless of active theme, and used that same hue for the cell text on top of the same-hue
  background (low contrast on big moves) — cell text now uses neutral ink since the background
  tint + sign already carry direction.
- `web/public/index.html`, `i18n.js`, `app.js`, `styles.css` — added a dedicated "Zone" column
  to the heatmap table. The quadrant badge used to live inside the same `<td>` as the theme name,
  so rows wrapped to 2 lines whenever name+badge text was too wide and stayed 1 line otherwise —
  inconsistent row heights. Moved the badge to its own column between name and 1D.
- `web/public/app.js`, `index.html` — made the new Theme and Zone columns sortable, same as the
  existing return columns. Theme sorts alphabetically (locale-aware, using the currently
  displayed language's name). Zone sorts by the same best-to-worst quadrant order already used
  in the Momentum Playbook (Leading, Improving, Weakening, Lagging); incomplete-data themes sort
  last.

**What worked:**
- Root-caused the Yahoo mismatch precisely (not just "close enough") by inspecting the actual
  cached price series and finding the adjustment boundary at the ex-dividend date.
- `tests/` suite (5 tests) still passes after every change today.
- Zone column verified with a headless Chromium run: all 36 rows report the identical height
  (43.375px) in both themes. First attempt at the fix (just moving the badge out) squeezed the
  name column and made long Thai names wrap instead — caught by measuring row heights again
  after the first "fix" instead of assuming it worked, then resolved with a min-width on the
  name column plus the existing horizontal scroll.
- Sortable Theme/Zone columns verified the same way: clicking Theme groups Thai names
  alphabetically, clicking Zone groups all 6 Leading themes first, then 14 Improving, 9
  Weakening, 6 Lagging (matches the Momentum Playbook's own grouping), zero console errors in
  every check today.

**Mistakes & recovery:**
- Assumed `auto_adjust=True` (which `spec.md` originally specified) was simply "more correct"
  total-return data; it works as designed, but nobody had flagged that it would diverge from
  Yahoo's own displayed price-chart %, which is what the user was actually comparing against.
- The Zone-column fix's first pass only moved the badge out but didn't check whether that
  changed anything else — it freed space that let long Thai names wrap for the first time,
  reproducing the same symptom (inconsistent row height) via a different cause. Caught by
  re-measuring row heights, not assumed from the screenshot alone.
- User reported the Zone-column fix "didn't show up" live. Queried GitHub's public REST API
  directly (`curl .../actions/runs`, no `gh` CLI or token needed for a public repo's run list,
  since `/actions/jobs/{id}/logs` returned 403 without an authenticated admin token) and found
  the `deploy-site` run for that commit had failed at `actions/deploy-pages@v4`. Initially
  guessed "transient Pages API hiccup" and asked the user to click "Re-run failed jobs" — that
  was the wrong call: it re-ran the upload+deploy job within the *same* run, and a leftover
  artifact from the original failed attempt was still present, so deploy-pages then found two
  artifacts both named `github-pages` and refused to pick one ("Multiple artifacts... Artifact
  count is 2"). The actual fix for this workflow shape (upload + deploy in one job) is to start
  a brand-new run (`workflow_dispatch` "Run workflow", or a new push) rather than re-running an
  existing one — a fresh run has no leftover artifact to collide with. User re-ran and it
  resolved; confirmed live afterward.

**Open TODOs / blockers:**
- [ ] If deploy-pages failures recur, consider whether `daily.yml`'s own deploy job and
      `deploy-site.yml` could ever collide on the shared `github-pages` environment (both target
      it; only `deploy-site.yml` has a `concurrency: group: pages` guard — `daily.yml` does not).
      Not the cause this time (that was the duplicate-artifact-from-partial-rerun issue above),
      but worth watching if it happens again.
- [ ] `TICKER_AUDIT_PLAN.md` still not executed (carried over from the earlier entry today).
- [ ] Leftover one-off debug scripts at repo root still not cleaned up (carried over).
- [ ] Still no explicit user confirmation that the RRG chart itself displays correctly in an
      ordinary (non-incognito) browser session — screenshots taken during this session look
      correct, and the user did confirm the Zone column is now visible live, but that's a
      different part of the page.

**Repro / verify:**
```bash
# unit tests
pytest tests/

# local dashboard preview
cd web/public && python -m http.server 8000

# check recent GitHub Actions runs without gh CLI / auth (public repo, public API)
curl -s "https://api.github.com/repos/Thailaxy/SectorRotation/actions/runs?per_page=10"
```

**Commits today (this entry):** `460d56a` `3493ec5` `26f1a14` `6b75163` `101dd07` `6861c31`
`8e75730` `131c428`

### 2026-07-04 (cont. 2) — Migrate hosting from GitHub Pages to Firebase Hosting

**Goal:** Move the dashboard's hosting from GitHub Pages to Firebase Hosting
(project `sectorrotation-546e0`, Spark/free tier). The data pipeline and frontend
are untouched — only the deploy target and related config/docs change.

**Changes:**
- `firebase.json` (new) — hosting config: `public: web/public`, with cache headers
  tuned for this app (`data.json` 5 min, `*.js`/`*.css` 1h + must-revalidate,
  `*.html` no-cache). Replaces Pages' blanket 10-min TTL with finer control.
- `.firebaserc` (new) — binds repo to project `sectorrotation-546e0`.
- `.github/workflows/deploy-site.yml` — replaced `actions/upload-pages-artifact`
  + `actions/deploy-pages` with `FirebaseExtended/action-hosting-deploy@v0` on the
  live channel. Trigger unchanged (push to `main` + `workflow_dispatch`).
- `.github/workflows/daily.yml` — removed the Pages deploy step but **kept a
  Firebase deploy step at the end of the build job.** Reason: the bot's
  `git push` uses GitHub's default `GITHUB_TOKEN`, and pushes made with that
  token deliberately do NOT trigger other workflows (GitHub anti-loop), so the
  push would not fire `deploy-site.yml` — daily data would never deploy. Inline
  deploy is the correct shape. (Also drops the now-unused `pages: write` /
  `id-token: write` permissions.)
- `.gitignore` — added `FIREBASE_SERVICE_ACCOUNT.json` + key-file patterns.
- `README.md` (architecture section) + `spec.md` (§6.3, §12) — swapped Pages for
  Firebase, added the `.web.app` URL.
- **Setup done by the user (one-time, manual):** created the
  `github-actions-deploy-752` service account with **Firebase Hosting Admin**
  role only (minimum privilege), generated a JSON key, and stored it as the
  `FIREBASE_SERVICE_ACCOUNT` GitHub Actions secret.

**Resolves open TODO from the earlier 2026-07-04 entry:** the
`concurrency: group: pages` collision risk between `daily.yml` and
`deploy-site.yml` (both previously targeted the shared `github-pages`
environment) is gone — Firebase Hosting deploys are atomic and have no shared
environment to collide on.

**What still needs manual follow-up (the user, ~2 min, once):**
- [ ] Push the migration, then in repo → Actions → `deploy-site` → Run workflow;
      open https://sectorrotation-546e0.web.app and verify the dashboard loads.
- [ ] After Firebase looks good, disable GitHub Pages: repo Settings → Pages →
      "Build and deployment" → Source = None. (Until then both sites stay live —
      zero downtime during the swap.)
- [ ] Optional: custom domain + DNS.

**Notes for next session:**
- The local `FIREBASE_SERVICE_ACCOUNT.json` at repo root is gitignored and safe
  to keep until after the first successful deploy, then should be deleted.
- This handoff entry was written *before* the migration was committed/pushed, so
  none of the file changes above are verified end-to-end against a real Firebase
  deploy yet — the live check is the open item above.

**Repro / verify (after pushing):**
```bash
# Trigger a deploy from the GitHub UI or REST API, then:
curl -sI https://sectorrotation-546e0.web.app/data.json | grep -i cache-control
# Expect: cache-control: public, max-age=300, must-revalidate
```
