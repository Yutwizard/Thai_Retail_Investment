"""Phase 3 — full four-sleeve portfolio simulation (Ch.7).

Sleeve A proxy: 60/40 global equity TRI (THB) / SET50 TRI less feeder TERs.
Sleeve B: the Phase 2 net-of-cost backtest equity curve.
Sleeve C: short-bond proxy less TER, plus MMF at THOR less fees.
Sleeve D: cash at THOR.

Combined at strategic weights with monthly rebalancing, the vol-targeting
overlay (trend scaled first, beta below m = 0.7) and the −15%/−7.5%
circuit breaker. Stress scenarios in Ch.7.3 are pass/fail, not informational.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .overlay import BreakerEvent, circuit_breaker, overlay_multiplier, split_multiplier


@dataclass
class SimulationResult:
    returns: pd.Series
    nav: pd.Series
    multiplier: pd.Series
    breaker_events: list[BreakerEvent]
    sleeve_returns: pd.DataFrame


def sleeve_a_proxy(global_tri_thb: pd.Series, set50_tri: pd.Series,
                   blend: tuple[float, float] = (0.60, 0.40),
                   ter_pa: float = 0.0) -> pd.Series:
    g = global_tri_thb.pct_change()
    t = set50_tri.pct_change()
    daily_ter = ter_pa / 252
    return (blend[0] * g + blend[1] * t - daily_ter).dropna()


def simulate(sleeve_returns: pd.DataFrame, weights: dict[str, float],
             vol_target: float = 0.10, beta_threshold: float = 0.70,
             breaker_trigger: float = -0.15, breaker_restore: float = -0.075) -> SimulationResult:
    """`sleeve_returns` columns: sleeve_a_beta, sleeve_b_trend,
    sleeve_c_ballast, sleeve_d_cash (daily returns, aligned)."""
    df = sleeve_returns.dropna()
    w = pd.Series(weights).reindex(df.columns).fillna(0.0)

    base = (df * w).sum(axis=1)
    m = overlay_multiplier(base, vol_target=vol_target).shift(1).fillna(1.0)

    # Apply the multiplier sleeve-by-sleeve: trend first, beta below threshold.
    scaled = df.copy()
    for date in df.index:
        trend_s, beta_s = split_multiplier(float(m.loc[date]), beta_threshold)
        scaled.loc[date, "sleeve_b_trend"] = df.loc[date, "sleeve_b_trend"] * trend_s
        scaled.loc[date, "sleeve_a_beta"] = df.loc[date, "sleeve_a_beta"] * beta_s

    rets = (scaled * w).sum(axis=1)
    nav = (1 + rets).cumprod()
    factor, events = circuit_breaker(nav, breaker_trigger, breaker_restore)

    # Risk-asset legs are scaled by the breaker factor from the next day on.
    risk_cols = ["sleeve_a_beta", "sleeve_b_trend"]
    f = factor.shift(1).fillna(1.0)
    final = scaled.copy()
    final[risk_cols] = scaled[risk_cols].mul(f, axis=0)
    final_rets = (final * w).sum(axis=1)
    final_nav = (1 + final_rets).cumprod()

    return SimulationResult(returns=final_rets, nav=final_nav, multiplier=m,
                            breaker_events=events, sleeve_returns=final)
