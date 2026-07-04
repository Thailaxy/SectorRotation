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
                    if close_col in df.columns.levels[0] and ticker in df[close_col].columns:
                        close_series.append(df[close_col][ticker].rename(ticker))
                        vol_series.append(df[vol_col][ticker].rename(ticker))
                except Exception as e:
                    print(f"  Failed {ticker}: {e}")
    except Exception as e:
        print(f"  Batch failed: {e}")
    if i + BATCH_SIZE < len(all_tickers):
        time.sleep(SLEEP_SEC)

if close_series:
    final_close = pd.concat(close_series, axis=1).ffill(limit=2)
    final_vol = pd.concat(vol_series, axis=1).ffill(limit=2)
else:
    raise RuntimeError("No data fetched — cache seed aborted.")

os.makedirs('cache', exist_ok=True)
final_close.to_csv('cache/prices.csv')
final_vol.to_csv('cache/volumes.csv')
print("Successfully generated real cache seed! SPY in columns:", 'SPY' in final_close.columns)
print("Total columns:", len(final_close.columns))

