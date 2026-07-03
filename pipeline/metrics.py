import numpy as np
import pandas as pd

def period_return(close_series, n_trading_days):
    if len(close_series) < n_trading_days + 1:
        return None
    try:
        val1 = close_series.iloc[-1]
        val0 = close_series.iloc[-1 - n_trading_days]
        if pd.isna(val1) or pd.isna(val0) or val0 == 0:
            return None
        return (val1 / val0 - 1) * 100
    except:
        return None

def calc_theme_return(close_df, constituents, n_days):
    rets = []
    for t in constituents:
        if t in close_df.columns:
            r = period_return(close_df[t].dropna(), n_days)
            if r is not None:
                rets.append(r)
    if not rets:
        return None
    return np.mean(rets)

def calc_pct_above_ma(close_df, constituents, ma_window=20):
    count_above = 0
    valid_count = 0
    for t in constituents:
        if t in close_df.columns:
            series = close_df[t].dropna()
            if len(series) >= ma_window:
                ma = series.rolling(ma_window).mean().iloc[-1]
                val = series.iloc[-1]
                if not pd.isna(val) and not pd.isna(ma):
                    valid_count += 1
                    if val > ma:
                        count_above += 1
    if valid_count == 0:
        return None
    return (count_above / valid_count) * 100

def calc_dollar_vol_ratio(close_df, vol_df, constituents, short=5, long=20):
    ratios = []
    for t in constituents:
        if t in close_df.columns and t in vol_df.columns:
            c = close_df[t]
            v = vol_df[t]
            dv = (c * v).dropna()
            if len(dv) >= long:
                short_ma = dv.rolling(short).mean().iloc[-1]
                long_ma = dv.rolling(long).mean().iloc[-1]
                if long_ma > 0 and not pd.isna(short_ma) and not pd.isna(long_ma):
                    ratios.append(short_ma / long_ma)
    if not ratios:
        return None
    return np.mean(ratios)

def classify(r, m):
    if r >= 100 and m >= 100: return "leading"
    if r >= 100 and m < 100: return "weakening"
    if r < 100 and m < 100: return "lagging"
    return "improving"

def calc_rrg(close_df, constituents, bench_series, smoothing=10, lookback_weeks=52, scale=10, tail_weeks=8):
    def to_weekly(df):
        if df.empty:
            return df
        # Workaround for pandas .resample() cython segfault in Python 3.14 alpha:
        # Filter to Fridays (dayofweek == 4) instead of resampling
        return df[df.index.dayofweek == 4].dropna(how='all')
    
    weekly_const = []
    for t in constituents:
        if t in close_df.columns:
            w = to_weekly(pd.DataFrame({'close': close_df[t]}))['close']
            if len(w) > 0 and w.iloc[0] > 0:
                norm_w = w / w.iloc[0] * 100
                weekly_const.append(norm_w)
    
    if not weekly_const:
        return None
    
    theme_weekly = pd.concat(weekly_const, axis=1).mean(axis=1)
    bench_weekly = to_weekly(bench_series)
    
    df_wk = pd.DataFrame({'theme': theme_weekly, 'bench': bench_weekly}).dropna()
    if len(df_wk) < lookback_weeks + 2:
        return None
    
    rs = df_wk['theme'] / df_wk['bench']
    rs_sm = rs.ewm(span=smoothing, adjust=False).mean()
    
    mean_r = rs_sm.rolling(lookback_weeks).mean()
    std_r = rs_sm.rolling(lookback_weeks).std()
    z_ratio = (rs_sm - mean_r) / std_r
    rs_ratio = 100 + scale * z_ratio
    
    mom = rs_ratio.diff()
    mean_m = mom.rolling(lookback_weeks).mean()
    std_m = mom.rolling(lookback_weeks).std()
    z_mom = (mom - mean_m) / std_m
    rs_momentum = 100 + scale * z_mom
    
    df_res = pd.DataFrame({
        'ratio': rs_ratio,
        'momentum': rs_momentum
    }).dropna()
    
    if len(df_res) == 0:
        return None
    
    tail = df_res.tail(tail_weeks)
    latest = tail.iloc[-1]
        
    return {
        "ratio": round(float(latest['ratio']), 2),
        "momentum": round(float(latest['momentum']), 2),
        "quadrant": classify(latest['ratio'], latest['momentum']),
        "tail": [{'ratio': round(r, 2), 'momentum': round(m, 2)} for r, m in zip(tail['ratio'], tail['momentum'])]
    }
