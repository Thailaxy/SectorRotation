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
end_date = pd.Timestamp.today().normalize()
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
                        # Both close AND volume must be non-empty. yfinance silently
                        # drops the Volume column for some tickers when ANY ticker
                        # in the batch hits a SystemError — even tickers whose Close
                        # data is fine (e.g. SPY when XLU/CVNA in same batch fail).
                        if (cand_close is not None and not cand_close.dropna().empty
                                and cand_vol is not None and not cand_vol.dropna().empty):
                            s_close = cand_close
                            s_vol = cand_vol
                    # Fallback: yfinance silently crashes for some tickers
                    # (SPY, SMH, ...) returning all-NaN columns, or drops Volume
                    # for the whole batch when one ticker errors. Hit Yahoo's
                    # chart API directly to recover them with both close + volume.
                    if s_close is None:
                        from pipeline.fetch import _fetch_via_yahoo_chart_api
                        fc, fv = _fetch_via_yahoo_chart_api(ticker, start_date, end_date)
                        if (fc is not None and not fc.dropna().empty
                                and fv is not None and not fv.dropna().empty):
                            print(f"  recovered {ticker} via Yahoo API fallback")
                            s_close = fc
                            s_vol = fv
                    if s_close is not None and s_vol is not None:
                        close_series.append(s_close.rename(ticker))
                        vol_series.append(s_vol.rename(ticker))
                except Exception as e:
                    print(f"  Failed {ticker}: {e}")
    except Exception as e:
        print(f"  Batch failed: {e}")
    if i + BATCH_SIZE < len(all_tickers):
        time.sleep(SLEEP_SEC)

if close_series:
    final_close = pd.concat(close_series, axis=1).ffill(limit=2)
    final_vol = pd.concat(vol_series, axis=1).ffill(limit=2)
    # Normalize the index: yfinance sometimes returns tz-aware or intraday
    # timestamps (e.g. '2026-07-03 01:00:00' from UTC offset confusion), which
    # corrupts joins later. Force clean midnight dates, no timezone.
    final_close.index = pd.to_datetime(final_close.index).tz_localize(None).normalize()
    final_vol.index = pd.to_datetime(final_vol.index).tz_localize(None).normalize()
    # Drop any duplicate dates (can happen when series with different tz handling
    # get concatenated), keeping the last value.
    final_close = final_close[~final_close.index.duplicated(keep='last')]
    final_vol = final_vol[~final_vol.index.duplicated(keep='last')]
else:
    raise RuntimeError("No data fetched — cache seed aborted.")

os.makedirs('cache', exist_ok=True)
final_close.to_csv('cache/prices.csv')
final_vol.to_csv('cache/volumes.csv')
print("Successfully generated real cache seed! SPY in columns:", 'SPY' in final_close.columns)
print("Total columns:", len(final_close.columns))

