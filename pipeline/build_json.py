import json
import datetime
import pandas as pd
from .metrics import calc_theme_return, calc_pct_above_ma, calc_dollar_vol_ratio, calc_rrg, period_return

def build_json(config, universe, close_df, vol_df, warnings):
    benchmark_ticker = config['benchmark']
    bench_series = close_df[benchmark_ticker].dropna() if benchmark_ticker in close_df.columns else None
    
    bench_ret_1d, bench_ret_1m, bench_ret_3m = None, None, None
    if bench_series is not None:
        bench_ret_1d = period_return(bench_series, config['returns']['d1'])
        bench_ret_1m = period_return(bench_series, config['returns']['m1'])
        bench_ret_3m = period_return(bench_series, config['returns']['m3'])
    
    as_of_date = ""
    if not close_df.empty:
        as_of_date = close_df.index[-1].strftime('%Y-%m-%d')
    
    data = {
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "as_of_date": as_of_date,
        "benchmark": benchmark_ticker,
        "benchmark_return_1D": round(bench_ret_1d, 2) if bench_ret_1d is not None else None,
        "benchmark_return_1M": round(bench_ret_1m, 2) if bench_ret_1m is not None else None,
        "benchmark_return_3M": round(bench_ret_3m, 2) if bench_ret_3m is not None else None,
        "config": {
            "rrg_tail_weeks": config['rrg']['tail_weeks'],
            "breadth_ma": config['breadth']['ma_window'],
            "rrg_scale": config['rrg']['scale']
        },
        "user_holdings": config.get('user_holdings', []),
        "themes": [],
        "warnings": warnings
    }
    
    for theme in universe.get('themes', []):
        theme_id = theme['id']
        t_type = theme.get('type', 'theme')
        consts = theme.get('constituents', [])
        
        ret_d1 = calc_theme_return(close_df, consts, config['returns']['d1'])
        ret_w1 = calc_theme_return(close_df, consts, config['returns']['w1'])
        ret_m1 = calc_theme_return(close_df, consts, config['returns']['m1'])
        ret_m3 = calc_theme_return(close_df, consts, config['returns']['m3'])
        
        ret_m1_vs_spy = None
        if ret_m1 is not None and bench_ret_1m is not None:
            ret_m1_vs_spy = ret_m1 - bench_ret_1m
            
        missing_any = False
        if consts:
            missing_any = any(t not in close_df.columns for t in consts)
            
        data_ok = bool(ret_m1 is not None) and not missing_any
            
        breadth_pct = None
        if t_type == 'theme':
            breadth_pct = calc_pct_above_ma(close_df, consts, config['breadth']['ma_window'])
            
        dv_ratio = calc_dollar_vol_ratio(close_df, vol_df, consts, config['dollar_volume']['short'], config['dollar_volume']['long'])
        
        rrg = None
        if bench_series is not None:
            rrg = calc_rrg(
                close_df, consts, bench_series,
                smoothing=config['rrg']['smoothing'],
                lookback_weeks=config['rrg']['lookback_weeks'],
                scale=config['rrg']['scale'],
                tail_weeks=config['rrg']['tail_weeks']
            )
            
        quadrant = rrg['quadrant'] if rrg else None
        
        theme_data = {
            "id": theme_id,
            "name_en": theme.get('name_en', ''),
            "name_th": theme.get('name_th', ''),
            "type": t_type,
            "data_ok": data_ok,
            "quadrant": quadrant,
            "returns": {
                "d1": round(ret_d1, 2) if ret_d1 is not None else None,
                "w1": round(ret_w1, 2) if ret_w1 is not None else None,
                "m1": round(ret_m1, 2) if ret_m1 is not None else None,
                "m3": round(ret_m3, 2) if ret_m3 is not None else None,
                "m1_vs_spy": round(ret_m1_vs_spy, 2) if ret_m1_vs_spy is not None else None,
            },
            "breadth_pct": round(breadth_pct, 1) if breadth_pct is not None else None,
            "dollar_vol_ratio": round(dv_ratio, 2) if dv_ratio is not None else None,
            "rrg": rrg,
            "constituents": consts,
            "ref_etfs": theme.get('ref_etfs', [])
        }
        
        data['themes'].append(theme_data)
        
    return data
