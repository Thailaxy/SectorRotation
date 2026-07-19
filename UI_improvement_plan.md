# UI Improvement Plan

Prioritized UI improvements from an investor's point of view, covering mobile and desktop.
Based on a live-site inspection (2026-07-19) of https://sectorrotation-wk.web.app at 1440px
(desktop) and 390px (iPhone-class, Playwright mobile emulation), plus a review of
`web/public/styles.css` and `web/public/app.js`.

Work top-down: Critical → Major → Moderate → Minor. Check items off as they are completed.

---

## Critical — mobile is effectively broken

### 1. [x] Fix horizontal page overflow on phones (page renders at 638px on a 390px screen)

**Symptom (confirmed with screenshots):** On a real phone the document is ~638px wide, so
the browser zooms out. The RRG chart is cut in half — the **Leading and Weakening quadrants
are off-screen**. The heatmap shows only the 1D and 1W columns (1M, 3M, vs-SPY cut off).
Breadth bars bleed past their card edges.

**Root cause (diagnosed):** `#heatmapTable` has `min-width: 600px`
(`styles.css`, mobile table section). The `.top-section` grid items use the CSS default
`min-width: auto`, so the table's minimum width propagates up through the grid instead of
triggering `.table-scroll`'s `overflow-x: auto`. The whole document widens to ~638px.

**Knock-on effect:** Because the layout viewport becomes 638px, the
`@media (max-width: 480px)` phone optimizations (stacked breadth cards, smaller fonts)
**never apply on real phones** — that CSS is currently dead code in practice.

**Fix:**
- Add `min-width: 0` to `.top-section` grid children (`.rrg-container`, `.heatmap-container`).
- Verified experimentally: this alone shrinks 638 → 625px, so 1–2 more offenders need the
  same treatment (find with the leaf-offender JS snippet below). Likely candidates: another
  container in the chain missing `min-width: 0`, or the ECharts canvas itself.
- The ECharts canvas initializes at 600px — call `rrgChart.resize()` after layout settles
  (the existing `window.resize` listener doesn't fire on load).

**Verify:** Playwright at `viewport 390x844, isMobile: true` →
`window.innerWidth === 390` and `document.documentElement.scrollWidth <= 390`.
Full-page screenshot must show all 4 RRG quadrants and the heatmap scrolling *inside* its
container.

```js
// Leaf-offender finder (run in page context, viewport 390 without isMobile):
document.querySelectorAll('body *').forEach(el => {
  const r = el.getBoundingClientRect();
  if (r.width > 392 && ![...el.children].some(c => c.getBoundingClientRect().width > 392))
    console.log(el, Math.round(r.width));
});
```

### 2. [x] Sticky first column + sticky header on the heatmap table (mobile)

Once fix #1 makes the table scroll internally, panning sideways to 3M/vs-SPY hides the
theme name — the investor can't tell which row they're reading.

**Fix:**
- `position: sticky; left: 0` on the name column (`td:first-child` / `th:first-child`)
  with an opaque background (`var(--panel)`) so numbers slide underneath.
- `position: sticky; top: 0` on `thead` — 36 rows is ~3 screens of scrolling with no
  column labels visible. (Also benefits desktop, see #5.)

**Verify:** Mobile emulation — pan the table right: theme names stay pinned; scroll down:
header row stays visible. Both themes (light/dark) — check the sticky cells aren't
transparent.

---

## Major — both mobile and desktop

### 3. [x] Make the RRG chart readable — 36 unlabeled spaghetti tails

The headline visualization: an investor cannot identify a single theme without hovering
each dot, and hover barely works on touch screens. Click-to-focus partially exists
(`selectedTheme` in `app.js`) but is undiscoverable.

**Options, roughly in order of value:**
- Label the head dot of each tail with a short name/ticker (ECharts series `label` on the
  last point; needs overlap handling — `labelLayout: { hideOverlap: true }`).
- Add a tappable legend or theme list that highlights one tail (make the existing
  click-to-focus discoverable, and workable on touch).
- Default to fewer series (e.g. Sector ETF filter or top-N movers) instead of all 36.
- Offer a tail-length toggle (2/4/8 weeks).

**Verify:** Screenshot both viewports — theme identity readable without interaction;
tapping a theme (chart or list) highlights its tail on mobile.

### 4. [x] Distinguish near-duplicate Theme vs ETF rows

"Energy (XLE)" vs "Energy", "Materials" vs "Materials (XLB)", "Staples" vs "Staples (XLP)"
appear side by side in the heatmap and Playbook with no visual distinction (Playbook has a
small "ETF" badge; heatmap has nothing). Two contradictory "Energy" rows erode trust.

**Fix:** Add a clear Theme/ETF tag in the heatmap table (the data already carries
`type: 'theme' | 'sector_etf'`), or a filter, or group the rows.

### 5. [x] Desktop: sticky table header + eliminate dead space under the RRG

Scrolling the 36-row heatmap on desktop immediately loses the column headers, and the
entire left half of the screen becomes empty (the RRG panel ends but its grid column keeps
its width).

**Fix:** Sticky `thead` (shared with #2). For the dead space: either make the RRG panel
`position: sticky; top: <header height>` so it stays visible while the table scrolls, or
cap the table height with internal vertical scroll.

### 6. [x] Remove the placeholder feedback entry

The public feedback table on the live site still shows
"Example User — This is an example entry… Delete it before going live…".
Instant credibility hit. Remove it from `web/public/feedback.json` (or seed with a real
entry).

---

## Moderate

### 7. [x] Header benchmark strip: hardcoded periods + awkward mobile wrap

The header shows SPY 1D/1M/3M regardless of the user's `selectedPeriods`, and on mobile
"3M: 5.57%" wraps onto its own line. Either sync with `selectedPeriods` or compact into
chips that wrap cleanly.

### 8. [x] Breadth & Volume section lacks in-place explanation

"Dollar Vol Ratio 0.82x" in red means nothing without the legend, which only lives in the
Playbook footnote. Add a one-line caption or info tooltip in the section itself. Sorting
is also absent here.

### 9. [x] RRG axis label clipping

The x-axis "100" label is clipped at the chart's right edge in both themes, and the top
"100" axis label collides with quadrant text on narrow screens. Adjust `grid.right` /
axis label margins.

---

## Minor

### 10. [x] Favicon + home-screen icon

No favicon — investors who pin the dashboard get a blank generic icon. Add a favicon and
a small PWA manifest (icon + `display: standalone`) so it opens full-screen from a phone
home screen.

### 11. [x] Momentum Playbook card heights (desktop)

Leading has 5 items, Improving 16 — large empty areas in the 4-column grid. Equalize with
scrollable card bodies or a two-column list inside wide cards.

### 12. [x] Link heatmap rows to the RRG

Rows highlight on hover but nothing is clickable. Tapping a row could highlight that theme
on the RRG (overlaps with #3's click-to-focus), tying the two views together.

---

## Suggested execution order

1. **#1 + #2** — one small CSS/JS change set, transforms the phone experience. Do first.
2. **#3** — RRG labels/focus (biggest investor-facing value after mobile works).
3. **#4 + #6** — quick wins.
4. **#5, #7–#9** — as time allows.
5. **#10–#12** — polish.

## Verification harness (reusable)

Local Playwright (installed at `~/Library/Caches/ms-playwright/`, driver via
`npx playwright` v1.61; `playwright-core` npm package needed in the script's cwd):

```bash
# Full-page mobile screenshot of the live site
npx playwright screenshot --viewport-size=390,844 --full-page \
  "https://sectorrotation-wk.web.app" mobile_full.png

# Local preview (uses committed data.json, no network fetch needed)
cd web/public && python -m http.server 8000
```

Check after every mobile fix: `document.documentElement.scrollWidth` at 390px viewport
must be ≤ 390.
