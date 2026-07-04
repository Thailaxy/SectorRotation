import yaml
import json
import os
from .fetch import fetch_data
from .build_json import build_json

def load_yaml(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def run_pipeline():
    config = load_yaml('config.yaml')
    universe = load_yaml('data/universe.yaml')
    etf100 = load_yaml('data/etf100.yaml')
    holdings = load_yaml('data/holdings.yaml')

    tickers = set()
    # 1) Universe constituents + ref_etfs
    for theme in universe.get('themes', []):
        for ticker in theme.get('constituents', []):
            tickers.add(ticker)
        for ref in theme.get('ref_etfs', []):
            tickers.add(ref['ticker'])
    # 2) All 100 ETF tickers (so we can compute per-ETF returns + RRG)
    for etf in etf100.get('etfs', []):
        tickers.add(etf['ticker'])
    # 3) All holdings tickers (so we can compute breadth for equity ETFs)
    for etf_ticker, holds in (holdings or {}).items():
        if isinstance(holds, list):
            for h in holds:
                tickers.add(h)

    tickers = list(tickers)
    print(f"Total unique tickers to fetch: {len(tickers)}")

    close_df, vol_df, warnings = fetch_data(
        tickers=tickers,
        benchmark=config['benchmark'],
        history_days=config['history_days'],
        retries=config['fetch']['retries'],
        retry_wait_sec=config['fetch']['retry_wait_sec']
    )

    data = build_json(config, universe, close_df, vol_df, warnings,
                      etf100=etf100, holdings=holdings)

    os.makedirs('web/public', exist_ok=True)

    with open('web/public/data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("Pipeline finished successfully. Wrote web/public/data.json")
    print(f"  themes: {len(data.get('themes', []))}, etfs: {len(data.get('etfs', []))}")
    for w in warnings:
        print("Warning:", w)

if __name__ == "__main__":
    run_pipeline()
