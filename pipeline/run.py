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
    
    tickers = set()
    for theme in universe.get('themes', []):
        for ticker in theme.get('constituents', []):
            tickers.add(ticker)
    
    tickers = list(tickers)
    
    close_df, vol_df, warnings = fetch_data(
        tickers=tickers,
        benchmark=config['benchmark'],
        history_days=config['history_days'],
        retries=config['fetch']['retries'],
        retry_wait_sec=config['fetch']['retry_wait_sec']
    )
    
    data = build_json(config, universe, close_df, vol_df, warnings)
    
    os.makedirs('web/public', exist_ok=True)
    
    with open('web/public/data.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print("Pipeline finished successfully. Wrote web/public/data.json")
    for w in warnings:
        print("Warning:", w)

if __name__ == "__main__":
    run_pipeline()
