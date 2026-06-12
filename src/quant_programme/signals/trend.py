"""Trend sleeve signal specification (Ch.6.1 — baseline, do not optimise).

Signal: sign of trailing 12-month (252 trading day) total return of the
back-adjusted series, computed at month-end settlement. 3m and 6m signals
are computed alongside for the ensemble robustness check only.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def ewma_volatility(returns: pd.Series, lam: float = 0.94,
                    window: int = 60, annualise: bool = True) -> pd.Series:
    """60-day exponentially weighted realised vol (λ = 0.94), annualised √252 (B.1).

    Variance recursion σ²_t = λ σ²_{t−1} + (1−λ) r²_t, seeded with the simple
    variance of the first `window` observations; values before a full seed
    window are NaN so nothing trades on an unseeded estimate.
    """
    r = returns.dropna()
    if len(r) < window:
        return pd.Series(np.nan, index=returns.index)
    var = np.empty(len(r))
    var[: window - 1] = np.nan
    v = float(r.iloc[:window].pow(2).mean())
    var[window - 1] = v
    sq = r.to_numpy() ** 2
    for t in range(window, len(r)):
        v = lam * v + (1 - lam) * sq[t]
        var[t] = v
    vol = pd.Series(np.sqrt(var), index=r.index)
    if annualise:
        vol = vol * np.sqrt(TRADING_DAYS)
    return vol.reindex(returns.index)


def trend_signal(prices: pd.Series, lookback_days: int = TRADING_DAYS) -> pd.Series:
    """Sign of trailing total return over `lookback_days`: +1 long, 0 flat/short side.

    Returns +1 / −1 (0 when insufficient history). The position rule
    (long/flat vs long/short) maps the sign to exposure downstream.
    """
    trailing = prices - prices.shift(lookback_days)
    sig = np.sign(trailing)
    return sig.fillna(0.0)


def month_end_signals(prices: pd.Series,
                      lookbacks: dict[str, int] | None = None) -> pd.DataFrame:
    """Signals sampled at month-end settlement, per Ch.6.1.

    Default lookbacks: 12m baseline plus 3m/6m for the ensemble check.
    """
    if lookbacks is None:
        lookbacks = {"3m": 63, "6m": 126, "12m": TRADING_DAYS}
    month_ends = prices.groupby(prices.index.to_period("M")).tail(1).index
    out = {name: trend_signal(prices, lb).loc[month_ends]
           for name, lb in lookbacks.items()}
    return pd.DataFrame(out)


def apply_position_rule(signal: pd.Series, rule: str = "long_flat") -> pd.Series:
    """Map signal sign to direction. (a) long/flat: long if positive, else flat;
    (b) long/short: long if positive, short if negative."""
    if rule == "long_flat":
        return signal.clip(lower=0.0)
    if rule == "long_short":
        return signal
    raise ValueError(f"Unknown position rule: {rule!r}")
