"""Section 6.4 unit test: signal sign on synthetic monotonic series."""

import numpy as np
import pandas as pd

from quant_programme.signals.trend import (
    apply_position_rule,
    ewma_volatility,
    month_end_signals,
    trend_signal,
)


def _dates(n: int) -> pd.DatetimeIndex:
    return pd.bdate_range("2015-01-01", periods=n)


def test_signal_positive_on_monotonic_uptrend():
    prices = pd.Series(np.linspace(100, 200, 600), index=_dates(600))
    sig = trend_signal(prices, lookback_days=252)
    assert (sig.iloc[252:] == 1.0).all()


def test_signal_negative_on_monotonic_downtrend():
    prices = pd.Series(np.linspace(200, 100, 600), index=_dates(600))
    sig = trend_signal(prices, lookback_days=252)
    assert (sig.iloc[252:] == -1.0).all()


def test_signal_zero_before_lookback_filled():
    prices = pd.Series(np.linspace(100, 200, 600), index=_dates(600))
    sig = trend_signal(prices, lookback_days=252)
    assert (sig.iloc[:252] == 0.0).all()


def test_long_flat_rule_clips_shorts():
    sig = pd.Series([1.0, -1.0, 0.0])
    assert apply_position_rule(sig, "long_flat").tolist() == [1.0, 0.0, 0.0]
    assert apply_position_rule(sig, "long_short").tolist() == [1.0, -1.0, 0.0]


def test_month_end_signals_sampled_at_month_ends():
    prices = pd.Series(np.linspace(100, 200, 600), index=_dates(600))
    df = month_end_signals(prices)
    assert set(df.columns) == {"3m", "6m", "12m"}
    # every sampled date is the last business day of its month within the series
    for d in df.index:
        same_month = prices.index[prices.index.to_period("M") == d.to_period("M")]
        assert d == same_month.max()


def test_ewma_vol_constant_returns():
    # constant daily return → vol converges to 0 contribution from variance of mean;
    # with identical returns, r² is constant so σ² = r² exactly.
    r = pd.Series(0.01, index=_dates(300))
    vol = ewma_volatility(r, window=60)
    assert np.isclose(vol.dropna().iloc[-1], 0.01 * np.sqrt(252))


def test_ewma_vol_nan_before_seed_window():
    r = pd.Series(np.random.default_rng(0).normal(0, 0.01, 300), index=_dates(300))
    vol = ewma_volatility(r, window=60)
    assert vol.iloc[:59].isna().all()
    assert vol.iloc[59:].notna().all()
