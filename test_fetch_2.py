from pipeline.fetch import fetch_data
print("Running fetch_data...")
close_df, vol_df, warnings = fetch_data(['AAPL'], 'SPY', 10)
print(f"Warnings: {warnings}")
print("Finished!")
