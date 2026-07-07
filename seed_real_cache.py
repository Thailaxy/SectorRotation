import yfinance as yf
import pandas as pd
import yaml
import datetime
import os
import time

with open('data/universe.yaml', 'r') as f:
    univ = yaml.safe_load(f)
with open('data/etf100.yaml', 'r') as f:
    etf100 = yaml.safe_load(f)
with open('data/holdings.yaml', 'r') as f:
    holdings = yaml.safe_load(f) or {}

tickers = ['SPY']
for t in univ['themes']:
    tickers.extend(t.get('constituents', []))
    for ref in t.get('ref_etfs', []):
        tickers.append(ref['ticker'])
# Include all 100 ETF tickers + holdings so the cache covers everything the
# daily pipeline will request.
for etf in etf100.get('etfs', []):
    tickers.append(etf['ticker'])
for holds in holdings.values():
    if isinstance(holds, list):
        tickers.extend(holds)
all_tickers = list(set(tickers))

# Match fetch.py: history_days is calendar days. 1825 ≈ 5Y (per config.yaml).
# Use the same UTC-anchored, exclusive end_date as fetch_data() so the cache
# seed covers the same range the daily pipeline will request.
from pipeline.fetch import _fetch_end_date
end_date = _fetch_end_date()
start_date = end_date - datetime.timedelta(days=1825)

# Match fetch.py exactly: auto_adjust=False, read 'Close' (not 'Adj Close').
# fetch.py:50-51 deliberately uses raw Close so returns match Yahoo's price
# chart (not total-return incl. dividends). The old seed used Adj Close, which
# mixed adjusted + unadjusted columns in the cache and produced wrong returns
# for any stock with a recent split/dividend. Aligned here.

BATCH_SIZE = 20
SLEEP_SEC = 2

close_series = []
vol_series = []

print(f"Fetching {len(all_tickers)} tickers in batches of {BATCH_SIZE}...")

# Critical tickers that MUST succeed — the benchmark + the 20 default ETFs.
# These get retried individually until they have full data.
CRITICAL_TICKERS = {
    'SPY',  # benchmark — pipeline can't compute vs_spy without it
    'QQQ', 'IWM', 'XLF', 'XLV', 'XLU', 'XLP', 'XLY', 'XLC', 'XLE',
    'XLK', 'XLI', 'SMH', 'GDX', 'EEM', 'HYG', 'TLT', 'VNQ', 'XBI', 'IBB',
}

def _try_fetch_ticker(ticker, start_date, end_date):
    """Try yfinance single-ticker download first; fall back to Yahoo chart API.
    Returns (close_series, vol_series) or (None, None)."""
    # Approach 1: single-ticker yfinance download (more reliable than batch for problem tickers)
    try:
        df = yf.download(ticker, start=start_date, end=end_date,
                         auto_adjust=False, progress=False)
        if df is not None and not df.empty:
            # Single-ticker download returns flat columns (no MultiIndex)
            if 'Close' in df.columns and 'Volume' in df.columns:
                c = df['Close'].dropna() if not isinstance(df.columns, pd.MultiIndex) else df['Close'][ticker].dropna()
                v = df['Volume'].dropna() if not isinstance(df.columns, pd.MultiIndex) else df['Volume'][ticker].dropna()
                if len(c) >= 600 and len(v) >= 600:
                    return c.rename(ticker), v.rename(ticker)
    except Exception:
        pass

    # Approach 2: Yahoo chart API fallback
    try:
        from pipeline.fetch import _fetch_via_yahoo_chart_api
        fc, fv = _fetch_via_yahoo_chart_api(ticker, start_date, end_date)
        if (fc is not None and not fc.dropna().empty
                and fv is not None and not fv.dropna().empty
                and len(fc.dropna()) >= 600):
            return fc.rename(ticker), fv.rename(ticker)
    except Exception:
        pass

    return None, None


# Build per-ticker dicts first.
close_dict_seed = {}
vol_dict_seed = {}

# Phase 1: batch download (efficient — gets most tickers in 27 batches)
for i in range(0, len(all_tickers), BATCH_SIZE):
    batch = all_tickers[i:i + BATCH_SIZE]
    batch_num = i // BATCH_SIZE + 1
    total_batches = (len(all_tickers) + BATCH_SIZE - 1) // BATCH_SIZE
    print(f"Batch {batch_num}/{total_batches}: {batch[:3]}...")
    try:
        df = yf.download(batch, start=start_date, end=end_date,
                         auto_adjust=False, progress=False)
        if df is not None and not df.empty:
            close_col = 'Close'
            vol_col = 'Volume'
            for ticker in batch:
                try:
                    s_close = None
                    s_vol = None
                    if close_col in df.columns.levels[0] and ticker in df[close_col].columns:
                        cand_close = df[close_col][ticker]
                        cand_vol = df[vol_col][ticker] if (vol_col in df.columns.levels[0] and ticker in df[vol_col].columns) else None
                        if (cand_close is not None and not cand_close.dropna().empty
                                and cand_vol is not None and not cand_vol.dropna().empty
                                and len(cand_close.dropna()) >= 600):
                            s_close = cand_close
                            s_vol = cand_vol
                    if s_close is not None and s_vol is not None:
                        close_dict_seed[ticker] = s_close.rename(ticker)
                        vol_dict_seed[ticker] = s_vol.rename(ticker)
                except Exception as e:
                    print(f"  Failed {ticker}: {e}")
    except Exception as e:
        print(f"  Batch failed: {e}")
    if i + BATCH_SIZE < len(all_tickers):
        time.sleep(SLEEP_SEC)

# Phase 2: retry critical tickers that didn't get full data via batch.
# yfinance's batch download is non-deterministic — SPY/QQQ/etc. fail randomly
# with SystemError. Single-ticker download + fallback is more reliable.
missing_critical = CRITICAL_TICKERS - set(close_dict_seed.keys())
print(f"\n=== Phase 2: retrying {len(missing_critical)} critical tickers individually ===")
for ticker in sorted(missing_critical):
    print(f"  Retrying {ticker}...")
    c, v = _try_fetch_ticker(ticker, start_date, end_date)
    if c is not None:
        close_dict_seed[ticker] = c
        vol_dict_seed[ticker] = v
        print(f"    ✓ {ticker}: {len(c.dropna())} rows")
    else:
        print(f"    ✗ {ticker}: failed all retries")

# Final summary
fetched_critical = CRITICAL_TICKERS & set(close_dict_seed.keys())
missing = CRITICAL_TICKERS - fetched_critical
if missing:
    print(f"\n⚠️  Still missing after retries: {sorted(missing)}")
else:
    print(f"\n✓ All {len(CRITICAL_TICKERS)} critical tickers have full data.")

close_series = list(close_dict_seed.values())
vol_series = list(vol_dict_seed.values())

if close_series:
    final_close = pd.concat(close_series, axis=1).ffill(limit=2)
    final_vol = pd.concat(vol_series, axis=1).ffill(limit=2)
    # Normalize the index: yfinance sometimes returns tz-aware or intraday
    # timestamps (e.g. '2026-07-03 01:00:00' from UTC offset confusion), which
    # corrupts joins later. Force clean midnight dates, no timezone.
    def _norm_idx(df):
        idx = pd.to_datetime(df.index)
        try:
            idx = idx.tz_convert(None)
        except (TypeError, AttributeError):
            pass
        df.index = idx.normalize()
        return df[~df.index.duplicated(keep='last')]
    final_close = _norm_idx(final_close)
    final_vol = _norm_idx(final_vol)
else:
    raise RuntimeError("No data fetched — cache seed aborted.")

os.makedirs('cache', exist_ok=True)
final_close.to_csv('cache/prices.csv')
final_vol.to_csv('cache/volumes.csv')
print("Successfully generated real cache seed! SPY in columns:", 'SPY' in final_close.columns)
print("Total columns:", len(final_close.columns))

