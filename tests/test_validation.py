"""Validation suite tests (Ch.5.3)."""

import pandas as pd

from quant_programme.data.continuous import build_continuous
from quant_programme.data.validation import (
    check_gaps,
    check_stale_prints,
    check_volume_sanity,
    run_suite,
)


def _clean_frame(n: int = 40) -> pd.DataFrame:
    dates = pd.bdate_range("2024-01-01", periods=n)
    expiry = dates[-1]
    return pd.DataFrame({
        "date": dates,
        "expiry": expiry,
        "settle": [1000.0 + i for i in range(n)],
        "volume": 1000,
        "open_interest": 5000,
    })


def test_gap_detection_flags_missing_day():
    cal = pd.bdate_range("2024-01-01", periods=40)
    prices = pd.Series(1.0, index=cal.delete(10))
    flags = check_gaps(prices, cal)
    assert len(flags) == 1 and flags[0].check == "gap_detection"


def test_stale_print_flags_three_identical_settles():
    df = _clean_frame()
    df.loc[5:7, "settle"] = 1005.0  # 3 identical consecutive, non-zero volume
    flags = check_stale_prints(df)
    assert any(f.check == "stale_print" for f in flags)


def test_volume_sanity():
    vol = pd.Series([100, 0, 50], index=pd.bdate_range("2024-01-01", periods=3))
    flags = check_volume_sanity(vol)
    assert len(flags) == 1


def test_clean_data_runs_green():
    raw = _clean_frame()
    cs = build_continuous(raw, "S50")
    cal = pd.DatetimeIndex(raw["date"])
    flags = run_suite(cs, raw, cal)
    assert flags == []
