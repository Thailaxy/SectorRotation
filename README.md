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

### 2026-07-05 — Prepared 100-ETF Heatmap Implementation Plan and Firebase Migration

**Goal:** Plan a major feature upgrade to allow users to select up to 20 ETFs from a predefined list of 100 ETFs to display on the Heatmap, with customizable return periods (1D, 1W, 1M, 3M, 6M, 1Y, 5Y), and migrate the hosting to Firebase. Designed for another AI agent (GLM5.2) to execute.

**Decisions & Plans:**
- **Firebase Migration**: Finalized a plan to migrate from GitHub Pages to Firebase Hosting to better manage cache headers and deployments.
- **ETF Selection Storage**: User selections (periods, ETFs, vs SPY benchmark) will be stored entirely in browser `localStorage`. No backend or login required.
- **Yahoo Finance Rate Limiting**: Mitigated by chunking ticker downloads in batches of 20 with a 2-second sleep, and utilizing the existing incremental cache logic.
- **Breadth Data (Holdings)**: Top 10 holdings for equity ETFs will be generated by a new one-time script (`scripts/generate_holdings.py`) using `yf.Ticker().funds_data.top_holdings` and saved to a static `data/holdings.yaml` file to avoid daily API scraping for holdings. A monthly GitHub Action cron job will update this static file.
- **Leveraged/Inverse ETFs**: Will inherit breadth data from their parent ETF via a new `breadth_source` field in config (e.g., TQQQ inherits from QQQ).
- **Default ETF Selection**: When switching to "ETF Mode", the initial 20 ETFs selected will mirror the current sector themes (e.g., SPY, QQQ, XLF, XLV, etc.).
- **Cache Storage Strategy**: Opted to move the `cache/` directory out of git commits to avoid repo bloat (15MB/day). Will use `actions/cache` in GitHub Actions with a 7-day LRU and a cold-start fallback (`seed_real_cache.py`).

**Mistakes Caught before Execution:**
- **Wrong yfinance API**: Corrected GLM5.2's assumption that `info.get('holdings')` works; mandated using `funds_data.top_holdings`.
- **auto_adjust flag**: Cautioned against blindly changing `auto_adjust=False` in `seed_real_cache.py` without verifying if `pipeline/fetch.py` expects adjusted or raw closes.
- **GitHub Action Cron Condition**: Corrected an invalid cron schedule condition (`github.event.schedule == '0 22 1-7 * 1'`) to a functional bash-based date check in the workflow step.

**Next Steps:**
- Hand off the implementation plan to GLM5.2 to begin Phase 1 (Data Foundation) and Phase 2 (Pipeline).

### 2026-07-07 — Fixed all-zero 1D returns (two interlocking bugs)

**Goal:** The day after launch, the 1D column showed 0.00% for every ETF/theme while 1W/1M/etc. worked. Diagnose and fix.

**What We Did:**
- Diagnosed via the live site, CI run logs, and the committed `data.json` (CI was demonstrably succeeding — pipeline finished, commit pushed, Firebase deployed — yet 1D stayed zero).
- Fixed two distinct bugs across three commits:
  - `64d5018` — Timezone fix in `pipeline/fetch.py`: replaced `pd.Timestamp.today()` (local-tz) with a new UTC-anchored `_fetch_end_date()` helper that adds 1 day (yfinance's `end` is exclusive). Applied in both `fetch.py` and `seed_real_cache.py`. Added 2 regression tests in `tests/test_fetch.py`.
  - `d121537` — Benchmark-anchored trim in `pipeline/fetch.py`: before `ffill(limit=2)`, drop trailing rows beyond the benchmark's (SPY's) last real close. Added 1 regression test reproducing the international-ticker contamination scenario.
- Updated `handoff.html` (full rewrite — the Jul 5 version still listed the 100-ETF heatmap as "upcoming", which has since shipped).

**Process:**
- Iterated empirically. The timezone fix was real but insufficient — after deploying it, 1D was still all-zero, which forced a deeper investigation. The real root cause was found by reproducing the exact CI output in pure pandas: an international ticker (already on "tomorrow" at 22:30 UTC) injected a future-date row; US tickers were NaN there; `ffill` copied their last close into it → last two rows identical → d1 = 0.
- Verified each fix with a targeted regression test and by inspecting CI's committed `data.json` after the run (d1 went from 95/95 zero to 0/93 zero; `as_of_date` correct).

**Key Decisions:**
- **Trim to the benchmark's last close (not "drop trailing NaN rows" generally).** The benchmark defines the app's "as of" date for a US-market focus. A generic trailing-NaN drop would break if SPY itself ever had a trailing NaN. Using `benchmark.last_valid_index()` (already `.dropna()`'d in `build_json`) is both correct and uses an existing value.
- **Keep `ffill(limit=2)`, don't remove it.** Considered the simpler "just delete ffill" but verified it changes 1W/1M/3M returns — ffill keeps row-counting aligned with trading-day-counting for those periods. Its legitimate job is filling interior gaps; the trim restricts it to exactly that.
- **Anchor `_fetch_end_date` to UTC, not local time.** CI runners are UTC; dev machines vary. The old `pd.Timestamp.today()` made CI silently produce data one day stale vs. local. Also `+1 day` because yfinance's `end` is exclusive.

**Mistakes & Lessons Learned:**
- **Declared victory too early on the timezone fix.** Shipped `64d5018`, told the user to trigger CI and go to work, and only discovered it was insufficient when they came back 14 hours later to an unchanged all-zero site. Lesson: when a bug has multiple plausible causes, verify the fix end-to-end against real output before declaring it done — don't reason from "the hypothesis sounds right."
- **The duration-based CI diagnosis was wrong.** Initially argued short CI runs (35–47s) "must be failures" and that CI wasn't producing data. It was — those were warm-cache runs. Should have checked the actual commit history (the bot commits are right there in `git log`) before theorizing about run durations.
- **Python 3.14 pandas instability cost real debugging time.** `tz_convert(None)`, `Timedelta` arithmetic, and `.resample()` all SIGBUS on pandas 2.2.2 + Python 3.14. The local dev environment couldn't run the full fetch path, forcing pure-pandas synthetic reproductions instead of just running the pipeline. CI (Python 3.11) was unaffected. Workarounds: `pd.Timestamp(ts.value)` to drop tz, `pd.DateOffset` instead of `pd.Timedelta`. Documented in `handoff.html` §3 and §5.
- **Root cause was non-obvious because two bugs compounded.** Either bug alone produced a milder symptom (timezone → one-day-stale, mostly invisible; future-date trim → only zero on the first run after a holiday). Both together produced the dramatic all-zero-1D that was reported. Reproducing the exact CI output in pure pandas was what finally isolated it.

**Verify (after deploy):**
```bash
# CI's committed data.json should now show real d1 values
git show origin/main:web/public/data.json | python -c "import json,sys; d=json.load(sys.stdin); print('as_of:', d['as_of_date']); print('benchmark d1:', d['benchmark_returns']['d1'])"
# Expect: as_of = latest US trading day, benchmark d1 != 0.0
# Then visit https://sectorrotation-wk.web.app/ — 1D column should show real dispersion.
```

### 2026-07-20 — Implemented all 12 items of the UI improvement plan (mobile was effectively broken)

**Goal:** Execute `UI_improvement_plan.md` (written 2026-07-19 from a live-site inspection at 1440px and 390px): fix the broken phone layout, make the RRG readable, and work through the moderate/minor polish items.

**What We Did:**
- Implemented every item, Critical → Minor, then verified with Playwright and deployed:
  - **Mobile overflow (#1):** added `min-width: 0` to `.top-section` grid children in `styles.css` and a next-frame `rrgChart.resize()` in `app.js`. Document width went 638px → exactly 390px on a 390px viewport; all four RRG quadrants and the full heatmap are now on-screen.
  - **Sticky heatmap (#2, #5):** sticky first column (`left: 0`, opaque `var(--panel)` + hairline shadow) and sticky `thead` (opaque panel base + gradient overlay), enabled by capping `.heatmap-container .table-scroll` at `max-height: 540px` with internal vertical scroll — which simultaneously removed the desktop dead space under the RRG (both top panels now measure exactly 741px).
  - **RRG readability (#3, #9):** labeled each tail's head dot (ticker for sector rows, theme name otherwise) with `labelLayout: { hideOverlap: true }` and a 2px text border; spotlighting hides other labels; widened `grid.right` to 45 and silenced the markLine's "100" end-labels that collided with axis labels.
  - **Heatmap ↔ RRG linking (#12):** clicking a theme row toggles `selectedTheme` and re-renders both views (widening the filter to "All" if the row's type was filtered out); chart clicks sync the row highlight back. Legend text now advertises the interaction (EN + TH).
  - **Theme/ETF disambiguation (#4):** outlined gray "ETF" badge (`.badge.etf`) on sector-ETF rows in the heatmap.
  - **Placeholder feedback (#6):** emptied `web/public/feedback.json`; the table shows its i18n empty state.
  - **Header strip (#7):** replaced hardcoded SPY 1D/1M/3M with `renderBenchChips()` — pill chips for whatever periods the user selected, wrapping cleanly on mobile, fed by `benchmark_returns` (already in `data.json`).
  - **Breadth section (#8):** in-place one-line legend (EN + TH `breadth_note`) and click-to-sort on all three columns.
  - **PWA (#10):** `favicon.svg` (four-quadrant RRG motif), generated `icon-192/512.png` + `apple-touch-icon.png` with a dependency-free Python PNG writer, `manifest.webmanifest` with `display: standalone`.
  - **Playbook heights (#11):** `.pb-list` capped at 300px with internal scroll on desktop.
- Checked off all 12 items in `UI_improvement_plan.md`.
- Updated `handoff.html` §2/§3/§8 (new files, the mobile-overflow and sticky-table gotchas, the Playwright verification harness).

**Process:**
- Worked in the plan's priority order, CSS first, then HTML, then `app.js`, then i18n strings and assets — verifying after each batch rather than at the end.
- Verified with local Playwright (`playwright-core` + cached Chromium) against `python -m http.server`: mobile emulation 390×844 `isMobile: true` asserting `scrollWidth ≤ 390`, the plan's leaf-offender finder, sticky-position deltas measured in page context, element screenshots of every section in both themes, and an ETF-mode toggle sanity check (20 rows, zero JS errors).

**Key Decisions:**
- **Capped the heatmap's height instead of making the RRG panel sticky** (the plan offered either for #5): one CSS change solves both the desktop dead space *and* gives the sticky `thead` a scroll container to stick to — the sticky-RRG alternative would have solved only the dead space.
- **Outline-style badge for the ETF tag** rather than reusing the filled gray `.badge.incomplete` look: it labels row *kind*, not momentum state, so it should not visually compete with the colored zone badges.
- **Dropped the bleed-to-edge negative margin on the heatmap scroller (mobile only):** rows would otherwise scroll visibly through the 12px gutter beside the sticky first column.
- **Labels: full theme names with `hideOverlap`, not top-N filtering.** Keeping all 36 series with overlap pruning preserves the "whole market at a glance" value; the tap-to-spotlight interaction covers dense regions.

**Mistakes & Lessons Learned:**
- **Fixing #1 exposed a latent bug in the previously-dead 480px CSS.** Once the viewport stopped inflating to 638px, the stacked breadth/feedback card layouts finally applied — and inherited the generic `.table-scroll table { min-width: 600px }`, rendering 600px-wide "cards" inside a 340px container. Fixed with `min-width: 0` on those tables at ≤480px. Lesson: when reviving media queries that never ran in production, re-test everything inside them — dead CSS accumulates untested interactions.
- **The plan's diagnosis was accurate and made execution nearly mechanical.** The one thing it under-specified ("1–2 more offenders need the same treatment") turned out to be nothing extra on the current codebase — the grid `min-width: 0` plus the chart resize sufficed. Verifying with the plan's own harness caught this early instead of chasing phantom offenders.

**Verify (after deploy):**
```bash
npx playwright screenshot --viewport-size=390,844 --full-page "https://sectorrotation-wk.web.app" mobile_check.png
# All 4 RRG quadrants visible, heatmap scrolls inside its card, labels on tail heads.
curl -s https://sectorrotation-wk.web.app/manifest.webmanifest | head -3
# Expect the PWA manifest, not a 404.
```
