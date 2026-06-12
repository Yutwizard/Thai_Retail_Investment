"""Transaction cost engine (Ch.6.2).

Costs are charged on every simulated transaction including rolls. All values
come from the Phase 0 cost register in config/parameters.yaml — the engine
raises MissingParameterError rather than use a published average.

Cost drag is reported separately as % p.a. of sleeve capital; budget ≤ 2%.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .config import InstrumentSpec


@dataclass(frozen=True)
class TradeCost:
    date: pd.Timestamp
    instrument: str
    contracts: int
    sides: int
    kind: str            # "signal" | "roll"
    cost_thb: float


def side_cost(spec: InstrumentSpec, contracts: int, roll: bool = False) -> float:
    """Commission + fees per side plus slippage in ticks, per contract."""
    ticks = spec.slippage_ticks_roll if roll else spec.slippage_ticks_normal
    per_contract = spec.require_commission() + ticks * spec.tick_value_thb
    return abs(contracts) * per_contract


def charge_signal_trade(spec: InstrumentSpec, date: pd.Timestamp,
                        delta_contracts: int) -> TradeCost | None:
    if delta_contracts == 0:
        return None
    return TradeCost(date=date, instrument=spec.code, contracts=abs(delta_contracts),
                     sides=1, kind="signal",
                     cost_thb=side_cost(spec, delta_contracts, roll=False))


def charge_rolls(spec: InstrumentSpec, roll_log: pd.DataFrame,
                 positions: pd.Series) -> list[TradeCost]:
    """Each roll-log entry is charged as a full round trip (2 sides) on the
    contracts held on the roll date, at the roll-slippage assumption."""
    costs: list[TradeCost] = []
    for _, ev in roll_log.iterrows():
        date = ev["date"]
        held = positions.asof(date) if len(positions) else 0
        held = 0 if pd.isna(held) else int(held)
        if held == 0:
            continue
        costs.append(TradeCost(
            date=date, instrument=spec.code, contracts=abs(held), sides=2, kind="roll",
            cost_thb=2 * side_cost(spec, held, roll=True),
        ))
    return costs


def cost_drag_pa(costs: list[TradeCost], sleeve_capital: float, years: float) -> float:
    """Total transaction costs / sleeve capital, annualised (B.5)."""
    if years <= 0:
        return 0.0
    return sum(c.cost_thb for c in costs) / sleeve_capital / years
