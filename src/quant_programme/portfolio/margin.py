"""Margin adequacy model (Ch.3.4, 7.4, B.4) — the critical Phase 0/3 item.

For every simulation day:
    required = Σ_i N_i × IM_stressed,i + adverse_days × vm_mult × σ_daily,THB
    available = cash buffer + same-day-instructed MMF (arriving T+1)

Stressed IM assumes TFEX raises initial margin by 50% mid-crisis at maximum
position count. The binding metric is the worst single-day gap; it must be
≤ 0 across all stress scenarios, with no forced Sleeve A sale.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from ..config import InstrumentSpec


@dataclass(frozen=True)
class MarginCheck:
    worst_gap_thb: float        # max(required − available); pass when ≤ 0
    worst_date: pd.Timestamp | None
    max_utilisation: float      # peak required / available
    passed: bool


def required_liquidity(positions: dict[str, pd.Series], specs: dict[str, InstrumentSpec],
                       daily_vol_thb: pd.Series,
                       stressed_im_multiplier: float = 1.5,
                       adverse_vm_days: int = 2,
                       adverse_vm_vol_multiplier: float = 3.0) -> pd.Series:
    idx = daily_vol_thb.index
    im = pd.Series(0.0, index=idx)
    for code, pos in positions.items():
        spec = specs[code]
        im += pos.abs().reindex(idx).fillna(0.0) * spec.require_initial_margin() \
              * stressed_im_multiplier
    vm = adverse_vm_days * adverse_vm_vol_multiplier * daily_vol_thb
    return im + vm


def check_adequacy(required: pd.Series, cash_buffer_thb: float,
                   mmf_balance_thb: float) -> MarginCheck:
    available = cash_buffer_thb + mmf_balance_thb
    gap = required - available
    worst = float(gap.max()) if len(gap) else 0.0
    worst_date = gap.idxmax() if len(gap) else None
    util = float((required / available).max()) if available > 0 and len(required) else float("inf")
    return MarginCheck(worst_gap_thb=worst, worst_date=worst_date,
                       max_utilisation=util, passed=worst <= 0)
