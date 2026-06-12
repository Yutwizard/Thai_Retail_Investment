"""Phase 2 trend-sleeve backtest engine (Ch.6).

Monthly rebalance on the first trading day using the prior month-end signal
and vol estimate; intra-month action only on a signal flip or a > 25% move
in the vol estimate. Every position change and every roll-log entry is
charged through the cost engine. Nothing is optimised here — the engine
exists to test whether the published anomaly survives Thai retail frictions.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from ..config import InstrumentSpec
from ..costs import TradeCost, charge_rolls, charge_signal_trade, cost_drag_pa
from ..data.continuous import ContinuousSeries
from ..signals.trend import apply_position_rule, ewma_volatility, trend_signal
from ..sizing import contract_count
from .metrics import TRADING_DAYS, summary


@dataclass
class InstrumentResult:
    positions: pd.Series                 # contracts held per day (signed)
    pnl_thb: pd.Series                   # daily mark-to-market P&L, gross
    costs: list[TradeCost] = field(default_factory=list)


@dataclass
class SleeveResult:
    per_instrument: dict[str, InstrumentResult]
    sleeve_capital: float
    gross_returns: pd.Series
    net_returns: pd.Series
    cost_drag_pa: float

    def report(self, thor_daily: pd.Series) -> dict[str, dict[str, float]]:
        return {
            "gross": summary(self.gross_returns, thor_daily),
            "net": summary(self.net_returns, thor_daily, cost_drag=self.cost_drag_pa),
        }


def _rebalance_dates(index: pd.DatetimeIndex) -> pd.DatetimeIndex:
    """First trading day of each month."""
    return index.to_series().groupby(index.to_period("M")).head(1).index


def run_instrument(cs: ContinuousSeries, spec: InstrumentSpec,
                   sleeve_capital: float, risk_share: float,
                   sleeve_vol_target: float = 0.12,
                   lookback_days: int = TRADING_DAYS,
                   position_rule: str = "long_flat",
                   vol_band: float = 0.25,
                   ewma_lambda: float = 0.94,
                   vol_window: int = 60,
                   granularity_max_overshoot: float = 1.5) -> InstrumentResult:
    prices = cs.prices
    raw = cs.raw_front
    rets = cs.returns
    vol = ewma_volatility(rets, lam=ewma_lambda, window=vol_window)
    direction = apply_position_rule(trend_signal(prices, lookback_days), position_rule)

    rebal = set(_rebalance_dates(prices.index))
    positions = pd.Series(0, index=prices.index, dtype=int)
    costs: list[TradeCost] = []

    held = 0
    vol_at_rebal = None
    dir_at_rebal = 0.0

    for i, date in enumerate(prices.index):
        if i == 0:
            positions.iloc[0] = 0
            continue
        # Decide using yesterday's information; trade at today's settlement.
        prev = prices.index[i - 1]
        sig = direction.loc[prev]
        v = vol.loc[prev]

        flip = sig != dir_at_rebal
        vol_moved = (vol_at_rebal is not None and pd.notna(v) and vol_at_rebal > 0
                     and abs(v / vol_at_rebal - 1) > vol_band)
        if date in rebal or flip or vol_moved:
            if pd.isna(v) or v <= 0 or sig == 0:
                target = 0
            else:
                sized = contract_count(risk_share, sleeve_vol_target, sleeve_capital,
                                       float(v), spec.point_value_thb,
                                       float(raw.loc[prev]),
                                       granularity_max_overshoot)
                target = int(sig) * (sized.contracts if sized.includable else 0)
            if target != held:
                cost = charge_signal_trade(spec, date, target - held)
                if cost:
                    costs.append(cost)
                held = target
            vol_at_rebal = None if pd.isna(v) else float(v)
            dir_at_rebal = sig
        positions.iloc[i] = held

    # P&L: contracts held over the day × point value × adjusted price change.
    pnl = positions.shift(1).fillna(0) * prices.diff().fillna(0.0) * spec.point_value_thb
    costs += charge_rolls(spec, cs.roll_log, positions)
    return InstrumentResult(positions=positions, pnl_thb=pnl, costs=costs)


def run_sleeve(series: dict[str, ContinuousSeries], specs: dict[str, InstrumentSpec],
               sleeve_capital: float, **kwargs) -> SleeveResult:
    n = len(series)
    results = {code: run_instrument(cs, specs[code], sleeve_capital,
                                    risk_share=1.0 / n, **kwargs)
               for code, cs in series.items()}

    pnl = sum(r.pnl_thb.reindex(_union_index(results)).fillna(0.0) for r in results.values())
    cost_series = pd.Series(0.0, index=pnl.index)
    all_costs: list[TradeCost] = []
    for r in results.values():
        all_costs += r.costs
        for c in r.costs:
            if c.date in cost_series.index:
                cost_series.loc[c.date] += c.cost_thb

    years = len(pnl) / TRADING_DAYS
    return SleeveResult(
        per_instrument=results,
        sleeve_capital=sleeve_capital,
        gross_returns=pnl / sleeve_capital,
        net_returns=(pnl - cost_series) / sleeve_capital,
        cost_drag_pa=cost_drag_pa(all_costs, sleeve_capital, years),
    )


def _union_index(results: dict[str, InstrumentResult]) -> pd.DatetimeIndex:
    idx = None
    for r in results.values():
        idx = r.pnl_thb.index if idx is None else idx.union(r.pnl_thb.index)
    return idx
