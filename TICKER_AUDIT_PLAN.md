# Ticker & ETF Universe Audit Plan

> For an AI agent to execute. **Read-only task — do not modify any existing file in this repo.**
> The only artifact this task should produce is a new report file (see "Output" below).

## Context

`data/universe.yaml` defines ~25 themes (equal-weight stock baskets) and 11 sector ETFs used by
this dashboard's daily data pipeline (`pipeline/fetch.py` fetches these tickers from Yahoo
Finance via yfinance). The list was drafted once and has not been re-verified against current
market reality since. `spec.md` section 19 ("Open Questions") already flags this as unverified:
tickers can get delisted, acquired, renamed, or have their symbol reassigned to a different
company entirely.

Read `data/universe.yaml` directly for the current, authoritative list of tickers — do not rely
on any list reproduced elsewhere (this plan intentionally does not duplicate it, to avoid drift).
Each theme entry has `constituents` (stocks) and `ref_etfs` (reference ETFs, informational only,
not fetched for calculations). There are also 11 standalone `type: sector_etf` entries near the
end of the file.

## What to verify, per ticker

For every ticker in `constituents`, `ref_etfs[].ticker`, and the `sector_etf` entries:

1. **Still actively traded** under this exact symbol on a US exchange (NYSE/NASDAQ/ARCA/etc.)
   today. Flag if: delisted, went private, acquired/merged into another company, bankrupt, or
   moved to OTC/pink sheets.
2. **Symbol reassignment risk** — the most dangerous failure mode: a ticker symbol getting
   recycled to an *unrelated* company after the original was delisted. If this happened, the
   pipeline would silently blend two different companies' price history under one symbol. Flag
   any ticker where the current company behind the symbol doesn't match the name implied by
   context (theme name, or the original company this was presumably meant to track).
3. **For `ref_etfs` and `sector_etf` tickers specifically**: confirm the ETF itself hasn't been
   liquidated/closed or merged into another fund.
4. **Share class sanity check**: note but do NOT flag as broken — e.g. `GOOGL` vs `GOOG` is an
   intentional choice already in the file, not a discrepancy to fix.

## What NOT to flag as broken

- The two intentional theme/sector-ETF name overlaps documented in `spec.md` section 17
  (`Materials` theme vs `xlf`/`xlb` sector ETF entries, `Staples` theme vs `xlp` sector ETF
  entry) — these are deliberate, separate entries by design.
- `GRID` appearing as a `ref_etf` under two different themes — also intentional/informational.

## Optional: freshness suggestions (separate from correctness)

Separately from the "is this broken" check, you may suggest additions/removals per theme if a
notable, well-established company clearly belongs in that theme and is missing (e.g. a company
that IPO'd or became prominent after this list was drafted). Keep this clearly separated from
verified breakage — these are opinions, not facts, and should not be presented with the same
confidence as a confirmed delisting.

## Method

- Use live web search / current data sources — do not rely on training-data memory for ticker
  status, since delistings and symbol changes happen continuously and this list needs
  *current* (as of today) verification.
- Cite a source (URL or search result) for every "BROKEN" finding — no unsourced claims in that
  section.

## Output

Write a single new markdown file at the repo root: `TICKER_AUDIT_REPORT.md`, with exactly three
sections:

```markdown
## BROKEN (verified — needs a code fix)
- TICKER (theme_id): what's wrong, source/evidence, suggested replacement if any

## UNCERTAIN (couldn't fully verify, needs human judgment)
- TICKER (theme_id): what's unclear and why

## SUGGESTIONS (optional freshness additions/removals, not correctness issues)
- theme_id: suggestion + rationale
```

Do not edit `data/universe.yaml`, `spec.md`, or any other existing file — this task is
verification and reporting only. A human will review `TICKER_AUDIT_REPORT.md` and decide what to
apply.
