import yaml
from pipeline.fetch import fetch_data

print("Loading yaml")
config = yaml.safe_load(open('config.yaml', 'r'))
universe = yaml.safe_load(open('data/universe.yaml', 'r'))

print("Extracting tickers")
tickers = set()
for theme in universe.get('themes', []):
    for ticker in theme.get('constituents', []):
        tickers.add(ticker)
tickers = list(tickers)
print(f"Got {len(tickers)} tickers")

print("Calling fetch_data")
close_df, vol_df, warnings = fetch_data(
    tickers=tickers,
    benchmark=config['benchmark'],
    history_days=config['history_days'],
    retries=config['fetch']['retries'],
    retry_wait_sec=config['fetch']['retry_wait_sec']
)
print("fetch_data returned!")
