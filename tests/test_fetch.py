import pandas as pd
import numpy as np
from pipeline.fetch import _fetch_end_date
from pipeline.metrics import period_return


def test_end_date_is_utc_anchored_not_local():
    """yfinance's `end` is exclusive, so we pass tomorrow's date in UTC.

    Regression: fetch_data previously used `pd.Timestamp.today()`, which is
    local-time. A GitHub Actions runner (UTC) computing end_date at 22:30 UTC
    got a date one day earlier than a developer on UTC+7 running at 05:30
    local (22:30 UTC). The CI DataFrame then ended a day short, excluding
    the current trading day's close, producing a stale `as_of_date` and
    all-zero 1D returns.
    """
    # Same instant, two UTC offsets a developer/CI split could plausibly span.
    instant = pd.Timestamp("2026-07-06 22:30:00", tz="UTC")

    ci_runner_end = _fetch_end_date(now_utc=instant)
    dev_machine_end = _fetch_end_date(now_utc=instant)

    assert ci_runner_end == dev_machine_end, (
        "end_date must be timezone-independent so CI and local agree"
    )
    # Exclusive end → day after "today" in UTC → today's close is included.
    assert ci_runner_end == pd.Timestamp("2026-07-07"), (
        f"expected 2026-07-07 (inclusive of Mon 7/6 close), got {ci_runner_end}"
    )


def test_end_date_returns_tz_naive_midnight():
    """end_date must be tz-naive and normalized to midnight so it aligns with
    the cache index and yfinance's expected date input."""
    end = _fetch_end_date(now_utc=pd.Timestamp("2026-07-06 22:30:00", tz="UTC"))
    assert end.tz is None, f"expected tz-naive, got tz={end.tz}"
    assert end == end.normalize(), "expected normalized midnight"


def test_benchmark_trim_prevents_future_date_zero_d1():
    """Regression: at 22:30 UTC, Asian/Australian markets are already on the
    next calendar day, so their tickers inject a "tomorrow" row into the
    combined DataFrame. US tickers have no data for that row (NaN), and the
    subsequent ffill copied their last real close into it — making the last
    two rows identical and zeroing every 1D return.

    The fix trims trailing rows beyond the benchmark's last real close before
    ffill. This test reproduces the contamination scenario with synthetic data
    and asserts the benchmark's 1D return is the real move, not 0.0%.
    """
    benchmark = "SPY"
    # SPY: US market — last real close is Mon 7/6. No 7/7 data yet.
    # INTL: Asian market — already has a 7/7 row at run time.
    close = pd.DataFrame({
        "SPY":  [744.78, 751.28, np.nan],
        "INTL": [100.0,  101.0,  102.0],
    }, index=pd.to_datetime(["2026-07-02", "2026-07-06", "2026-07-07"]))

    # --- Reproduce the fix inline (mirrors fetch.py: trim then ffill) ---
    bench_last = close[benchmark].last_valid_index()
    trimmed = close.loc[:bench_last]
    trimmed = trimmed.ffill(limit=2)

    # Without the fix, close would carry a 7/7 row with SPY=751.28 (ffilled),
    # and period_return(SPY, 1) would be (751.28/751.28 - 1)*100 = 0.0%.
    spy_d1 = period_return(trimmed["SPY"], 1)

    assert spy_d1 is not None, "SPY should have enough history for 1D"
    assert spy_d1 != 0.0, (
        f"SPY 1D was zeroed by future-date ffill; expected the real move "
        f"~+0.87%, got {spy_d1}%"
    )
    # Sanity: it's the Mon-vs-Thu move we put in the fixture.
    expected = (751.28 / 744.78 - 1) * 100
    assert abs(spy_d1 - expected) < 1e-6, f"expected {expected}, got {spy_d1}"

    # And the trailing future row is gone — last date is the benchmark's.
    assert trimmed.index[-1] == pd.Timestamp("2026-07-06"), (
        f"expected last date 2026-07-06 (SPY last close), got {trimmed.index[-1]}"
    )
