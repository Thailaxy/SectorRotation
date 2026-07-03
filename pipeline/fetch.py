import os
import time
import pandas as pd
import yfinance as yf

def fetch_data(tickers, benchmark, history_days, retries=3, retry_wait_sec=5):
    cache_file = "cache/prices.csv"
    vol_cache_file = "cache/volumes.csv"
    cache_df = None
    vol_cache_df = None
    
    if os.path.exists(cache_file):
        try:
            cache_df = pd.read_csv(cache_file, index_col=0, parse_dates=True)
        except Exception:
            pass
            
    if os.path.exists(vol_cache_file):
        try:
            vol_cache_df = pd.read_csv(vol_cache_file, index_col=0, parse_dates=True)
        except Exception:
            pass

    import datetime
    end_date = pd.Timestamp.today().normalize()
    start_date = end_date - datetime.timedelta(days=history_days)
    
    all_tickers = list(set(tickers + [benchmark]))
    warnings = []
    
    df = None
    for attempt in range(retries):
        try:
            print(f"Fetching data from yfinance (attempt {attempt+1}/{retries})...")
            import requests
            session = requests.Session()
            session.headers.update(
                {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
            )
            df = yf.download(all_tickers, start=start_date, end=end_date, auto_adjust=True, session=session)
            break
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(retry_wait_sec)
    
    close_dict = {}
    vol_dict = {}
    
    if df is not None and not df.empty:
        close_col = 'Adj Close' if 'Adj Close' in df.columns.levels[0] else 'Close'
        vol_col = 'Volume'
        for ticker in all_tickers:
            try:
                if close_col in df.columns.levels[0] and ticker in df[close_col].columns:
                    close_dict[ticker] = df[close_col][ticker]
                    vol_dict[ticker] = df[vol_col][ticker]
                else:
                    raise KeyError(ticker)
            except Exception:
                warnings.append(f"QUANTUM: ticker {ticker} could not be fetched from yfinance.")
    else:
        warnings.append("yfinance returned empty or failed completely.")
    
    final_close = pd.DataFrame(close_dict)
    final_vol = pd.DataFrame(vol_dict)
    
    if cache_df is not None:
        for ticker in all_tickers:
            if ticker not in final_close.columns or final_close[ticker].isna().all():
                if ticker in cache_df.columns:
                    final_close[ticker] = cache_df[ticker]
                    
    if vol_cache_df is not None:
        for ticker in all_tickers:
            if ticker not in final_vol.columns or final_vol[ticker].isna().all():
                if ticker in vol_cache_df.columns:
                    final_vol[ticker] = vol_cache_df[ticker]

    os.makedirs("cache", exist_ok=True)
    if not final_close.empty:
        final_close.to_csv(cache_file)
    if not final_vol.empty:
        final_vol.to_csv(vol_cache_file)
    
    final_close = final_close.ffill(limit=2)
    final_vol = final_vol.ffill(limit=2)
    
    return final_close, final_vol, warnings
