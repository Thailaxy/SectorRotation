import os
import time
import pandas as pd
import yfinance as yf


def _fetch_end_date(now_utc=None):
    """Return the exclusive end_date for yfinance downloads, anchored to UTC.

    yfinance's `end` is exclusive (pandas convention), so to include today's
    close we pass tomorrow's date. We anchor to UTC (not local time) so CI
    runners and developer machines compute the same date regardless of their
    timezone — the previous code used `pd.Timestamp.today()`, which made the
    GitHub Actions runner (UTC) cut off one day earlier than a +07 developer
    machine, producing a stale `as_of_date` and all-zero 1D returns.
    """
    ts = now_utc if now_utc is not None else pd.Timestamp.utcnow()
    # Drop tz info. We avoid tz_convert(None): on Python 3.14 it triggers a
    # SIGBUS in pandas' tz-conversion C-extension. pd.Timestamp(ts.value)
    # reconstructs a tz-naive timestamp from the epoch, sidestepping the bug
    # while producing identical results across pandas versions.
    ts = pd.Timestamp(ts.value)
    # DateOffset (not Timedelta) avoids a second C-ext SIGBUS on 3.14 when
    # adding to a tz-naive Timestamp. Equivalent result.
    return ts.normalize() + pd.DateOffset(days=1)


def _fetch_via_yahoo_chart_api(ticker, start_date, end_date):
    """
    Fallback for tickers where yfinance's bulk download crashes (known bug
    for some ETFs like SMH — throws SystemError on parse). Hits Yahoo's chart
    API directly via curl_cffi and assembles a close/volume DataFrame.

    Returns (close_series, vol_series) or (None, None) on failure.
    """
    try:
        from curl_cffi import requests as curl_requests
        session = curl_requests.Session(impersonate="chrome")
        url = "https://query1.finance.yahoo.com/v8/finance/chart/" + ticker
        params = {
            "period1": int(pd.Timestamp(start_date).timestamp()),
            "period2": int(pd.Timestamp(end_date).timestamp()),
            "interval": "1d",
        }
        r = session.get(url, params=params, timeout=20)
        if r.status_code != 200:
            return None, None
        result = r.json().get("chart", {}).get("result", [None])[0]
        if not result:
            return None, None
        ts = result.get("timestamp", [])
        quote = result.get("indicators", {}).get("quote", [{}])[0]
        closes = quote.get("close", [])
        volumes = quote.get("volume", [])
        if not ts or not closes:
            return None, None
        idx = pd.to_datetime(ts, unit="s")
        close_s = pd.Series(closes, index=idx, name=ticker)
        vol_s = pd.Series(volumes, index=idx, name=ticker)
        return close_s, vol_s
    except Exception as e:
        print(f"  -> Yahoo chart API fallback failed for {ticker}: {e!r}")
        return None, None


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
    end_date = _fetch_end_date()
    start_date = end_date - datetime.timedelta(days=history_days)
    
    all_tickers = list(set(tickers + [benchmark]))
    warnings = []

    # Batch tickers in groups of 20 to avoid tripping Yahoo's bot detection.
    # A single yf.download() with ~480 tickers (universe + 100 ETFs + holdings)
    # gets rate-limited or returns partial/empty data; batching with a small
    # sleep between groups keeps the request pattern human-ish.
    BATCH_SIZE = 20
    SLEEP_SEC = 2

    df_parts = []
    last_err = None
    for batch_start in range(0, len(all_tickers), BATCH_SIZE):
        batch = all_tickers[batch_start:batch_start + BATCH_SIZE]
        attempt_df = None
        for attempt in range(retries):
            try:
                print(f"Fetching batch {batch_start // BATCH_SIZE + 1}/"
                      f"{(len(all_tickers) + BATCH_SIZE - 1) // BATCH_SIZE} "
                      f"({len(batch)} tickers, attempt {attempt+1}/{retries})...")
                from curl_cffi import requests as curl_requests
                session = curl_requests.Session(impersonate="chrome")
                b_df = yf.download(batch, start=start_date, end=end_date,
                                   auto_adjust=False, session=session)
                if b_df is not None and not b_df.empty:
                    attempt_df = b_df
                    break
            except Exception as e:
                print(f"  -> batch attempt {attempt+1} failed: {e!r}")
                last_err = e
            if attempt < retries - 1:
                time.sleep(retry_wait_sec)
        if attempt_df is not None:
            df_parts.append(attempt_df)
        else:
            warnings.append(f"Batch starting at {batch_start} ({batch[:3]}...) "
                            f"failed all retries. Last error: {last_err!r}")
        if batch_start + BATCH_SIZE < len(all_tickers):
            time.sleep(SLEEP_SEC)

    # Concatenate all batches. If all batches failed, df_parts is empty → df=None.
    if df_parts:
        # Use outer union of dates so a missing day in one batch doesn't drop
        # rows from another. Multi-index columns align automatically per ticker.
        df = pd.concat(df_parts, axis=1)
    else:
        df = None

    print(f"  -> combined shape {df.shape if df is not None else None}, "
          f"empty={df.empty if df is not None else True}")
    
    close_dict = {}
    vol_dict = {}

    if df is not None and not df.empty:
        # Plain 'Close' (split-adjusted, not dividend-adjusted) so returns match
        # what Yahoo Finance's price chart shows, not total-return incl. dividends.
        close_col = 'Close'
        vol_col = 'Volume'
        for ticker in all_tickers:
            try:
                if close_col in df.columns.levels[0] and ticker in df[close_col].columns:
                    s = df[close_col][ticker]
                    # Some tickers (e.g. SMH) come back with a column of all-NaN
                    # because yfinance's parser crashed on them silently. Detect
                    # that and fall back to the Yahoo chart API.
                    if s.dropna().empty:
                        raise KeyError(ticker)
                    close_dict[ticker] = s
                    vol_dict[ticker] = df[vol_col][ticker]
                else:
                    raise KeyError(ticker)
            except Exception:
                # Try the Yahoo chart API fallback before giving up on this ticker.
                fc, fv = _fetch_via_yahoo_chart_api(ticker, start_date, end_date)
                if fc is not None and not fc.dropna().empty:
                    print(f"  -> recovered {ticker} via Yahoo chart API fallback "
                          f"({len(fc.dropna())} rows)")
                    close_dict[ticker] = fc
                    vol_dict[ticker] = fv
                else:
                    warnings.append(f"QUANTUM: ticker {ticker} could not be fetched from yfinance.")
    else:
        warnings.append("yfinance returned empty or failed completely.")
    
    final_close = pd.DataFrame(close_dict)
    final_vol = pd.DataFrame(vol_dict)

    # Normalize indexes: yfinance sometimes returns tz-aware or intraday
    # timestamps which then fail to align with cache data (tz-naive midnight).
    # Force everything to clean tz-naive midnight before merging.
    def _normalize_idx(df):
        if df is None or df.empty:
            return df
        # tz_convert(None) converts tz-aware → UTC naive; tz_localize(None) is a
        # no-op on tz-naive. Use a try/except to handle both safely.
        idx = pd.to_datetime(df.index)
        try:
            idx = idx.tz_convert(None)
        except (TypeError, AttributeError):
            pass
        df = df.copy()
        df.index = idx.normalize()
        return df[~df.index.duplicated(keep='last')]

    final_close = _normalize_idx(final_close)
    final_vol = _normalize_idx(final_vol)
    cache_df = _normalize_idx(cache_df)
    vol_cache_df = _normalize_idx(vol_cache_df)

    # Merge cache as FALLBACK ONLY. The previous bug: combine_first preferred
    # cache values where cache was non-null, even when fresh data existed. That
    # meant stale cache entries (e.g. 6 rows of SPY at $720) survived even when
    # the live fetch had clean data. New rule: only use cache to FILL NaN gaps
    # in the live data, never to overwrite.
    if cache_df is not None:
        for ticker in all_tickers:
            if ticker in cache_df.columns:
                if ticker not in final_close.columns:
                    # Ticker entirely missing from live → use cache entirely.
                    final_close[ticker] = cache_df[ticker].reindex(final_close.index)
                else:
                    # Ticker exists in live → only fill NaN gaps from cache.
                    live = final_close[ticker]
                    cache_aligned = cache_df[ticker].reindex(final_close.index)
                    final_close[ticker] = live.where(live.notna(), cache_aligned)

    if vol_cache_df is not None:
        for ticker in all_tickers:
            if ticker in vol_cache_df.columns:
                if ticker not in final_vol.columns:
                    final_vol[ticker] = vol_cache_df[ticker].reindex(final_vol.index)
                else:
                    live = final_vol[ticker]
                    cache_aligned = vol_cache_df[ticker].reindex(final_vol.index)
                    final_vol[ticker] = live.where(live.notna(), cache_aligned)

    os.makedirs("cache", exist_ok=True)
    if not final_close.empty:
        final_close.to_csv(cache_file)
    if not final_vol.empty:
        final_vol.to_csv(vol_cache_file)

    # Trim trailing rows the benchmark hasn't traded yet. The pipeline runs at
    # 22:30 UTC, when Asian/Australian markets are already on "tomorrow" from a
    # US perspective; their tickers inject a future-date row that US tickers
    # have no data for. Without this trim, ffill below copies each US ticker's
    # last real close into that future row, making the last two rows identical
    # and zeroing every 1D return. Anchoring to the benchmark's last real close
    # restricts ffill to interior gaps (its intended purpose).
    if benchmark in final_close.columns:
        bench_last = final_close[benchmark].last_valid_index()
        if bench_last is not None:
            final_close = final_close.loc[:bench_last]
            final_vol = final_vol.loc[:bench_last]

    final_close = final_close.ffill(limit=2)
    final_vol = final_vol.ffill(limit=2)
    
    return final_close, final_vol, warnings
