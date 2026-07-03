import pandas as pd
from pipeline.fetch import fetch_data
close_df, vol_df, _ = fetch_data(['NVDA', 'AMD'], 'SPY', 400)
print(close_df.columns)
