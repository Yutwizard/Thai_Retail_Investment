"""Automated validation suite (Ch.5.3) — run on every data refresh.

Each check returns ValidationFlag entries; an empty result is a green run.
Signal runs must be gated on a green (or fully-explained) validation pass —
data faults reaching the signal stage are a zero-tolerance Phase 4 error.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from .continuous import ContinuousSeries


@dataclass(frozen=True)
class ValidationFlag:
    check: str
    date: pd.Timestamp | None
    detail: str


def check_gaps(prices: pd.Series, trading_calendar: pd.DatetimeIndex) -> list[ValidationFlag]:
    """No missing trading days vs the exchange calendar."""
    missing = trading_calendar.difference(prices.index)
    return [ValidationFlag("gap_detection", d, "missing trading day") for d in missing]


def check_stale_prints(raw: pd.DataFrame, run_length: int = 3) -> list[ValidationFlag]:
    """Flag >= `run_length` identical consecutive front settles with non-zero volume."""
    flags: list[ValidationFlag] = []
    df = raw.sort_values("date")
    same = (df["settle"].diff() == 0) & (df["volume"] > 0)
    run = 0
    for date, is_same in zip(df["date"], same):
        run = run + 1 if is_same else 0
        if run >= run_length - 1:
            flags.append(ValidationFlag("stale_print", date,
                                        f"{run + 1} identical consecutive settlements"))
    return flags


def check_roll_jumps(cs: ContinuousSeries, max_daily_move: float = 0.10) -> list[ValidationFlag]:
    """Adjusted series must show no artificial jump at roll dates beyond a
    genuine market move; on failure re-derive the gap from the roll log."""
    flags: list[ValidationFlag] = []
    rets = cs.returns
    for date in cs.roll_log.get("date", []):
        if date in rets.index and abs(rets.loc[date]) > max_daily_move:
            flags.append(ValidationFlag("roll_jump", date,
                                        f"adjusted return {rets.loc[date]:.2%} on roll date"))
    return flags


def check_spot_futures_basis(futures_front: pd.Series, spot: pd.Series,
                             band: float = 0.05) -> list[ValidationFlag]:
    """USD/THB futures basis vs BOT spot must sit inside a plausible carry band."""
    aligned = pd.concat([futures_front, spot], axis=1, join="inner")
    basis = aligned.iloc[:, 0] / aligned.iloc[:, 1] - 1.0
    bad = basis[basis.abs() > band]
    return [ValidationFlag("spot_futures_basis", d, f"basis {v:.2%} outside ±{band:.0%}")
            for d, v in bad.items()]


def check_volume_sanity(raw_front_volume: pd.Series) -> list[ValidationFlag]:
    """Front-month volume must be > 0 on every included day."""
    bad = raw_front_volume[raw_front_volume <= 0]
    return [ValidationFlag("volume_sanity", d, "front-month volume <= 0") for d in bad.index]


def reconciliation_sample(prices: pd.Series, n: int = 10,
                          seed: int | None = None) -> pd.Series:
    """Pick n random dates per instrument for manual reconciliation against
    TFEX official settlement pages. Any mismatch mandates a full re-pull."""
    return prices.sample(n=min(n, len(prices)), random_state=seed).sort_index()


def run_suite(cs: ContinuousSeries, raw_front: pd.DataFrame,
              trading_calendar: pd.DatetimeIndex,
              spot: pd.Series | None = None) -> list[ValidationFlag]:
    flags: list[ValidationFlag] = []
    flags += check_gaps(cs.prices, trading_calendar)
    flags += check_stale_prints(raw_front)
    flags += check_roll_jumps(cs)
    flags += check_volume_sanity(raw_front.set_index("date")["volume"])
    if spot is not None:
        flags += check_spot_futures_basis(cs.raw_front, spot)
    return flags
