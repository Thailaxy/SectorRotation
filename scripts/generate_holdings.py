"""
Refresh top-10 holdings for all equity ETFs in data/etf100.yaml.

Designed to run monthly (1st Monday) via the daily GitHub Actions workflow.
Reads existing data/holdings.yaml, fetches fresh holdings via yfinance's
funds_data.top_holdings, and writes back. Preserves manual edits by only
updating tickers where yfinance returns data.

Usage:
    python scripts/generate_holdings.py
"""
import sys
import time
import yaml
import yfinance as yf
from pathlib import Path

ETFS_PATH = Path(__file__).resolve().parent.parent / "data" / "etf100.yaml"
HOLDINGS_PATH = Path(__file__).resolve().parent.parent / "data" / "holdings.yaml"
TOP_N = 10
SLEEP_SEC = 1.5  # gentle on yfinance between requests


def load_etfs_to_refresh():
    """Return tickers that need their own holdings (Group A + GDX)."""
    with open(ETFS_PATH) as f:
        d = yaml.safe_load(f)
    # Group A: has_breadth=true AND no breadth_source (own holdings)
    # Group B (breadth_source) inherits from parent — not refreshed here
    return sorted([
        e["ticker"] for e in d["etfs"]
        if e.get("has_breadth", False) and "breadth_source" not in e
    ])


def load_existing_holdings():
    """Read existing holdings.yaml; tolerate missing file (cold start)."""
    if not HOLDINGS_PATH.exists():
        return {}
    with open(HOLDINGS_PATH) as f:
        d = yaml.safe_load(f) or {}
    return d


def fetch_top_holdings(ticker):
    """
    Use yf.Ticker(x).funds_data.top_holdings (the documented attribute).
    Returns list of symbol strings (top N), or None if unavailable.

    NOTE: funds_data returns None for non-fund tickers or on yfinance failures.
    ARKK and some active ETFs may return None — caller leaves them unchanged.

    BUGFIX: top_holdings is a DataFrame whose INDEX is the symbol (ticker),
    not a column. The columns are ['Name', 'Holding Percent']. Earlier code
    looked for a 'Symbol' column that didn't exist, so it returned None for
    every ETF and the script silently populated nothing.
    """
    try:
        t = yf.Ticker(ticker)
        fd = t.funds_data
        if fd is None:
            return None
        # top_holdings DataFrame: index=Symbol, columns=['Name', 'Holding Percent']
        th = fd.top_holdings
        if th is None or th.empty:
            return None
        # Symbol is the INDEX. Use th.index, not a 'Symbol' column.
        symbols = th.index.dropna().astype(str).tolist()
        return symbols[:TOP_N]
    except Exception as e:
        print(f"  ! {ticker}: error fetching holdings: {e!r}", file=sys.stderr)
        return None


def main():
    etfs = load_etfs_to_refresh()
    print(f"Refreshing holdings for {len(etfs)} ETFs...")

    existing = load_existing_holdings()
    updated = dict(existing)  # preserve existing entries

    fetched = 0
    skipped = 0
    for i, ticker in enumerate(etfs, 1):
        print(f"[{i}/{len(etfs)}] {ticker}...", end=" ")
        holdings = fetch_top_holdings(ticker)
        if holdings is None or len(holdings) == 0:
            print("no data (skipped)")
            skipped += 1
            # leave existing entry untouched if present, else add empty
            if ticker not in updated:
                updated[ticker] = []
        else:
            print(f"got {len(holdings)} holdings: {', '.join(holdings[:3])}...")
            updated[ticker] = holdings
            fetched += 1
        time.sleep(SLEEP_SEC)

    # Write back sorted by ticker for stable diffs
    HOLDINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(HOLDINGS_PATH, "w") as f:
        f.write("# Top-10 holdings per equity ETF.\n")
        f.write("# Auto-populated monthly by scripts/generate_holdings.py (1st Monday).\n")
        f.write("# Empty list = breadth will show N/A for this ETF until populated.\n\n")
        for ticker in sorted(updated.keys()):
            syms = updated[ticker]
            if not syms:
                f.write(f"{ticker}: []\n")
            else:
                f.write(f"{ticker}:\n")
                for s in syms:
                    f.write(f"  - {s}\n")

    print(f"\nDone. Fetched: {fetched}, skipped: {skipped}, total in file: {len(updated)}")
    print(f"Wrote: {HOLDINGS_PATH}")


if __name__ == "__main__":
    main()
