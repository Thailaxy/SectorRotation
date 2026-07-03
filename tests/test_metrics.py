import pytest
import pandas as pd
import numpy as np
from pipeline.metrics import period_return, calc_pct_above_ma, calc_dollar_vol_ratio, classify, calc_rrg

def test_period_return():
    s = pd.Series([100.0, 105.0, 110.0])
    r = period_return(s, 2)
    assert np.isclose(r, 10.0)

def test_pct_above_ma():
    df = pd.DataFrame({
        'A': [100, 100, 110], 
        'B': [100, 100, 110], 
        'C': [100, 100, 110], 
        'D': [100, 100, 110], 
        'E': [100, 100, 90],  
        'F': [100, 100, 90],  
        'G': [100, 100, 90],  
        'H': [100, 100, 90],  
    })
    constituents = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H']
    pct = calc_pct_above_ma(df, constituents, ma_window=2)
    assert pct == 50.0

def test_dollar_vol_ratio():
    close_df = pd.DataFrame({'A': [10, 10, 10, 10]})
    vol_df = pd.DataFrame({'A': [100, 100, 200, 200]})
    ratio = calc_dollar_vol_ratio(close_df, vol_df, ['A'], short=2, long=4)
    assert np.isclose(ratio, 1.33333333333)

def test_classify():
    assert classify(100, 100) == "leading"
    assert classify(101, 101) == "leading"
    assert classify(100, 99) == "weakening"
    assert classify(99, 99) == "lagging"
    assert classify(99, 100) == "improving"

def test_rrg_reproducible():
    dates = pd.date_range(start='2023-01-01', periods=60, freq='W-FRI')
    close_df = pd.DataFrame({'A': np.linspace(100, 150, 60)}, index=dates)
    bench_series = pd.Series(np.linspace(100, 120, 60), index=dates)
    
    rrg1 = calc_rrg(close_df, ['A'], bench_series, smoothing=2, lookback_weeks=10, scale=10, tail_weeks=5)
    rrg2 = calc_rrg(close_df, ['A'], bench_series, smoothing=2, lookback_weeks=10, scale=10, tail_weeks=5)
    
    assert rrg1 == rrg2
    assert rrg1 is not None
    assert 'quadrant' in rrg1
    assert 'ratio' in rrg1
    assert 'momentum' in rrg1
    assert len(rrg1['tail']) == 5
