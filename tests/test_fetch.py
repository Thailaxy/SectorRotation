import pandas as pd
from pipeline.fetch import _fetch_end_date


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
