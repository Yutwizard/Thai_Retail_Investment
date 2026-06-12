"""Roll methodology tests (Ch.5.2) — the highest-risk step in the build.
An incorrect adjustment fabricates or destroys trend P&L silently."""

import numpy as np
import pandas as pd

from quant_programme.data.continuous import build_continuous


def _two_expiry_frame() -> pd.DataFrame:
    """Front month expiring mid-sample with a constant +5 contango gap."""
    dates = pd.bdate_range("2024-01-01", periods=40)
    exp1, exp2 = dates[19], dates[39]
    rows = []
    for i, d in enumerate(dates):
        price = 1000.0 + i  # smooth uptrend
        if d <= exp1:
            rows.append({"date": d, "expiry": exp1, "settle": price,
                         "volume": 1000, "open_interest": 5000})
        rows.append({"date": d, "expiry": exp2, "settle": price + 5.0,
                     "volume": 100 if d < dates[10] else 2000, "open_interest": 4000})
    return pd.DataFrame(rows)


def test_roll_triggers_on_volume_crossover():
    cs = build_continuous(_two_expiry_frame(), "S50")
    assert len(cs.roll_log) == 1
    # volume crossover happens at dates[10]
    assert cs.roll_log.iloc[0]["date"] == pd.bdate_range("2024-01-01", periods=40)[10]


def test_panama_gap_applied_to_history():
    cs = build_continuous(_two_expiry_frame(), "S50")
    gap = cs.roll_log.iloc[0]["gap"]
    assert gap == 5.0
    roll_date = cs.roll_log.iloc[0]["date"]
    # Before the roll, adjusted = raw + gap; after, adjusted = raw.
    pre = cs.prices.index < roll_date
    assert np.allclose(cs.prices[pre], cs.raw_front[pre] + gap)
    assert np.allclose(cs.prices[~pre], cs.raw_front[~pre])


def test_no_artificial_jump_at_roll():
    cs = build_continuous(_two_expiry_frame(), "S50")
    # underlying trend is +1/day; the adjusted series must show the same move
    # through the roll date, with no +5 jump.
    diffs = cs.prices.diff().dropna()
    assert np.allclose(diffs, 1.0)


def test_roll_on_t_minus_5_without_volume_crossover():
    df = _two_expiry_frame()
    # keep second-month volume permanently below front month
    df.loc[df["expiry"] == df["expiry"].max(), "volume"] = 10
    df.loc[(df["expiry"] == df["expiry"].min()), "volume"] = 1000
    cs = build_continuous(df, "S50", days_before_expiry=5)
    assert len(cs.roll_log) == 1
    dates = pd.bdate_range("2024-01-01", periods=40)
    # rolls when ≤ 5 sessions remain to the old expiry (dates[19])
    assert cs.roll_log.iloc[0]["date"] == dates[15]
