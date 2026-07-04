# Ticker & ETF Universe Audit Report

## BROKEN (verified — needs a code fix)

- **GOLD** (gold_miners): **Symbol reassignment risk triggered.** The original intended company, Barrick Gold Corporation, changed its name to Barrick Mining Corporation and moved its NYSE ticker symbol from `GOLD` to `B` on May 9, 2025. Subsequently, A-Mark Precious Metals rebranded to Gold.com, Inc. and claimed the `GOLD` ticker on December 2, 2025. If left unchanged, the data pipeline will blend the price history of the gold miner with the bullion retailer under a single symbol.
  - **Evidence/Source**: [Barrick Mining Corporation Name & Ticker Change (May 2025)](https://www.barrick.com), [Gold.com, Inc. Rebrand and Ticker Change (Dec 2025)](https://www.gold.com).
  - **Suggested replacement**: Replace `GOLD` with `B` to accurately track Barrick Mining Corporation.

## UNCERTAIN (couldn't fully verify, needs human judgment)

- None. All other 192 tickers (including reference and sector ETFs) successfully mapped to their expected active companies and funds. 

*(Note: `MSTR` is now Strategy Inc. and `NXT` is now Nextpower Inc. following rebranding events in 2025, but they both retained their original operations and ticker symbols, so they do not break the pipeline).*

## SUGGESTIONS (optional freshness additions/removals, not correctness issues)

- **semiconductors**: Consider adding **ARM** (Arm Holdings). Since its IPO, it has established itself as one of the most critical semiconductor architecture designers globally, heavily tied to the AI build-out, making it highly relevant to an equal-weight semiconductor theme.
