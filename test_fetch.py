import yfinance as yf
print("Calling yf.download")
df = yf.download(
    tickers=['AAPL', 'MSFT', 'GOOG'],
    period="1y",
    interval="1d",
    group_by="column",
    auto_adjust=False,
    prepost=False,
    threads=True
)
print("Finished yf.download")
print(df.head())
