import yfinance as yf
df = yf.download(['NVDA', 'AMD', 'SPY', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'META', 'TSLA', 'JPM', 'JNJ', 'V', 'PG', 'UNH', 'HD', 'MA', 'BAC', 'DIS', 'CVX', 'HD'], period='1d', threads=False)
print("Shape:", df.shape)
print("Empty?", df.empty)
