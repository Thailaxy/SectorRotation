import json
import datetime
import pandas as pd
from .metrics import calc_theme_return, calc_pct_above_ma, calc_dollar_vol_ratio, calc_rrg, period_return

# All return periods computed for every theme / ETF. Keys match the
# frontend's `selectedPeriods` toggle set.
ALL_PERIODS = ['d1', 'w1', 'm1', 'm3', 'm6', 'y1', 'y5']


def _returns_for(constituents, close_df, returns_cfg):
    """Compute mean return across `constituents` for every configured period."""
    out = {}
    for p in ALL_PERIODS:
        n = returns_cfg.get(p)
        if n is None:
            out[p] = None
            continue
        r = calc_theme_return(close_df, constituents, n)
        out[p] = round(r, 2) if r is not None else None
    return out


def _vs_spy(returns_obj, bench_returns_obj):
    """Subtract benchmark from each period. Inputs are dicts keyed by period."""
    out = {}
    for p in ALL_PERIODS:
        a = returns_obj.get(p)
        b = bench_returns_obj.get(p)
        out[p] = round(a - b, 2) if (a is not None and b is not None) else None
    return out


def _data_ok_for_etf(ticker, close_df):
    """An ETF is data_ok if its close series exists and has at least one value."""
    if ticker not in close_df.columns:
        return False
    s = close_df[ticker].dropna()
    return len(s) > 0


def build_json(config, universe, close_df, vol_df, warnings, etf100=None, holdings=None):
    benchmark_ticker = config['benchmark']
    bench_series = close_df[benchmark_ticker].dropna() if benchmark_ticker in close_df.columns else None

    # Benchmark returns for every period — used for ETF vs_spy and the header strip.
    bench_returns_obj = {}
    if bench_series is not None:
        for p in ALL_PERIODS:
            n = config['returns'].get(p)
            r = period_return(bench_series, n) if n is not None else None
            bench_returns_obj[p] = round(r, 2) if r is not None else None

    as_of_date = ""
    if not close_df.empty:
        as_of_date = close_df.index[-1].strftime('%Y-%m-%d')

    data = {
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "as_of_date": as_of_date,
        "benchmark": benchmark_ticker,
        # Backward-compat flat fields (keep during transition; remove later)
        "benchmark_return_1D": bench_returns_obj.get('d1'),
        "benchmark_return_1M": bench_returns_obj.get('m1'),
        "benchmark_return_3M": bench_returns_obj.get('m3'),
        # New: full per-period benchmark returns
        "benchmark_returns": bench_returns_obj,
        "config": {
            "rrg_tail_weeks": config['rrg']['tail_weeks'],
            "breadth_ma": config['breadth']['ma_window'],
            "rrg_scale": config['rrg']['scale']
        },
        "user_holdings": config.get('user_holdings', []),
        "themes": [],
        "etfs": [],
        "warnings": warnings
    }

    # ─────────── THEMES ───────────
    for theme in universe.get('themes', []):
        theme_id = theme['id']
        t_type = theme.get('type', 'theme')
        consts = theme.get('constituents', [])

        returns_obj = _returns_for(consts, close_df, config['returns'])
        vs_spy_obj = _vs_spy(returns_obj, bench_returns_obj)

        missing_any = False
        if consts:
            missing_any = any(t not in close_df.columns for t in consts)

        data_ok = bool(returns_obj.get('m1') is not None) and not missing_any

        breadth_pct = None
        if t_type == 'theme':
            breadth_pct = calc_pct_above_ma(close_df, consts, config['breadth']['ma_window'])

        dv_ratio = calc_dollar_vol_ratio(close_df, vol_df, consts,
                                         config['dollar_volume']['short'],
                                         config['dollar_volume']['long'])

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
                **returns_obj,
                # Backward-compat: keep flat m1_vs_spy alongside the new vs_spy object.
                # Remove this field once the frontend is confirmed on vs_spy.
                "m1_vs_spy": vs_spy_obj.get('m1'),
                "vs_spy": vs_spy_obj,
            },
            "breadth_pct": round(breadth_pct, 1) if breadth_pct is not None else None,
            "dollar_vol_ratio": round(dv_ratio, 2) if dv_ratio is not None else None,
            "rrg": rrg,
            "constituents": consts,
            "ref_etfs": theme.get('ref_etfs', [])
        }

        data['themes'].append(theme_data)

    # ─────────── ETFs (top-100 list) ───────────
    holdings = holdings or {}
    for etf in (etf100 or {}).get('etfs', []):
        ticker = etf['ticker']
        # Use the ETF's own series (single ticker) for returns / RRG.
        etf_consts = [ticker]
        returns_obj = _returns_for(etf_consts, close_df, config['returns'])
        vs_spy_obj = _vs_spy(returns_obj, bench_returns_obj)

        data_ok = _data_ok_for_etf(ticker, close_df)

        # Breadth: use breadth_source parent's holdings, else own holdings, else None.
        breadth_pct = None
        breadth_constituents = None
        if etf.get('has_breadth', False):
            source = etf.get('breadth_source')
            if source:
                breadth_constituents = holdings.get(source, [])
            else:
                breadth_constituents = holdings.get(ticker, [])
            if breadth_constituents:
                breadth_pct = calc_pct_above_ma(close_df, breadth_constituents,
                                                 config['breadth']['ma_window'])

        dv_ratio = calc_dollar_vol_ratio(close_df, vol_df, etf_consts,
                                         config['dollar_volume']['short'],
                                         config['dollar_volume']['long'])

        rrg = None
        if bench_series is not None:
            rrg = calc_rrg(
                close_df, etf_consts, bench_series,
                smoothing=config['rrg']['smoothing'],
                lookback_weeks=config['rrg']['lookback_weeks'],
                scale=config['rrg']['scale'],
                tail_weeks=config['rrg']['tail_weeks']
            )

        quadrant = rrg['quadrant'] if rrg else None

        etf_data = {
            "ticker": ticker,
            "name": etf.get('name', ''),
            "theme_label": etf.get('theme', ''),
            "rank": etf.get('rank'),
            "has_breadth": etf.get('has_breadth', False),
            "data_ok": data_ok,
            "quadrant": quadrant,
            "returns": {
                **returns_obj,
                "vs_spy": vs_spy_obj,
            },
            "breadth_pct": round(breadth_pct, 1) if breadth_pct is not None else None,
            "dollar_vol_ratio": round(dv_ratio, 2) if dv_ratio is not None else None,
            "rrg": rrg,
        }

        data['etfs'].append(etf_data)

    return data
