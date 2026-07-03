import pandas as pd
from pipeline.fetch import fetch_data
import yaml
with open('data/universe.yaml', 'r') as f:
    univ = yaml.safe_load(f)
tickers = ['SPY']
for t in univ['themes']:
    tickers.extend(t.get('constituents', []))
    for ref in t.get('ref_etfs', []):
        tickers.append(ref['ticker'])
tickers = list(set(tickers))

cache_file = "cache/prices.csv"
cache_df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
print("Cache df shape:", cache_df.shape)
print("SPY in cache:", 'SPY' in cache_df.columns)
print("SPY missing:", cache_df['SPY'].isna().all())
