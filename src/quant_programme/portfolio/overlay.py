"""Portfolio-level risk overlay (Ch.2.2, B.3) — two rules that sit above
all sleeves and override them.

1. Volatility targeting (Moreira–Muir): m = min(1.0, σ_target / σ_60d),
   recomputed monthly with a 25% intra-month band; scale the trend sleeve
   first, the beta sleeve only when m < 0.7.
2. Drawdown circuit breaker: at −15% from the high-water mark, cut gross
   exposure by 50% (trend positions first; never sell tax-wrapped funds);
   restore full exposure only when drawdown is back inside −7.5%.
   Mechanical and non-negotiable.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ..signals.trend import ewma_volatility


def overlay_multiplier(portfolio_returns: pd.Series, vol_target: float = 0.10,
                       window: int = 60) -> pd.Series:
    """m = min(1.0, σ_target / σ_realised), daily series."""
    vol = ewma_volatility(portfolio_returns, window=window)
    return (vol_target / vol).clip(upper=1.0)


def split_multiplier(m: float, beta_threshold: float = 0.70) -> tuple[float, float]:
    """Allocate the multiplier across sleeves: (trend_scale, beta_scale).

    The trend sleeve absorbs the reduction first (cheapest to adjust);
    the beta sleeve is scaled only once m < beta_threshold.
    """
    if pd.isna(m) or m >= 1.0:
        return 1.0, 1.0
    if m >= beta_threshold:
        return m, 1.0
    return m, m / beta_threshold


@dataclass(frozen=True)
class BreakerEvent:
    date: pd.Timestamp
    action: str          # "trigger" | "restore"
    drawdown: float


def circuit_breaker(nav: pd.Series, trigger: float = -0.15, restore: float = -0.075,
                    cut_fraction: float = 0.50) -> tuple[pd.Series, list[BreakerEvent]]:
    """Exposure factor series (1.0 normal, 1−cut_fraction while tripped) plus
    an auditable event log of every trigger and restore."""
    hwm = nav.cummax()
    dd = nav / hwm - 1
    factor = pd.Series(1.0, index=nav.index)
    events: list[BreakerEvent] = []
    tripped = False
    for date, d in dd.items():
        if not tripped and d <= trigger:
            tripped = True
            events.append(BreakerEvent(date, "trigger", float(d)))
        elif tripped and d >= restore:
            tripped = False
            events.append(BreakerEvent(date, "restore", float(d)))
        factor.loc[date] = 1.0 - cut_fraction if tripped else 1.0
    return factor, events
