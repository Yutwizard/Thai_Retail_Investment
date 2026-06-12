"""Continuous contract construction (Ch.5.2) — the highest-risk step in the build.

Roll trigger: first day the second month's volume exceeds the front month's,
OR five trading days before expiry, whichever comes first.

Adjustment: panama/difference back-adjustment — on the roll date compute
gap = settle(new front) − settle(old front) and add it to ALL history before
the roll date. Never ratio adjustment (difference preserves tick economics
for the cost model).

The series is rebuilt from raw on every run (never appended), and every roll
is written to an auditable roll log re-used by the cost engine to charge
roll round trips.
"""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class RollEvent:
    date: pd.Timestamp
    old_expiry: pd.Timestamp
    new_expiry: pd.Timestamp
    old_settle: float
    new_settle: float

    @property
    def gap(self) -> float:
        return self.new_settle - self.old_settle


@dataclass
class ContinuousSeries:
    instrument: str
    prices: pd.Series          # back-adjusted settlement series, indexed by date
    raw_front: pd.Series       # unadjusted front-month settles (for sanity checks)
    roll_log: pd.DataFrame     # columns: date, old_expiry, new_expiry, old_settle, new_settle, gap

    @property
    def returns(self) -> pd.Series:
        # Difference-adjusted series can pass through zero at long horizons;
        # returns are computed on price changes over the unadjusted price base,
        # which is the standard treatment for panama-adjusted futures.
        return (self.prices.diff() / self.raw_front.shift(1)).dropna()


def build_continuous(raw: pd.DataFrame, instrument: str,
                     days_before_expiry: int = 5) -> ContinuousSeries:
    """Build the back-adjusted continuous series from a long-format frame
    of all expiries (columns: date, expiry, settle, volume, open_interest)."""
    raw = raw.sort_values(["date", "expiry"])
    dates = raw["date"].drop_duplicates().sort_values().tolist()
    by_date = {d: g.set_index("expiry") for d, g in raw.groupby("date")}

    front_settles: list[float] = []
    front_dates: list[pd.Timestamp] = []
    rolls: list[RollEvent] = []
    current: pd.Timestamp | None = None

    for d in dates:
        g = by_date[d]
        listed = g.index.sort_values()
        listed = listed[listed >= d]
        if len(listed) == 0:
            continue
        if current is None or current not in g.index or current < d:
            current = listed[0]

        # Roll decision while a second month exists
        later = listed[listed > current]
        if len(later) > 0:
            second = later[0]
            sessions_to_expiry = sum(1 for x in dates if d <= x <= current)
            vol_crossover = g.loc[second, "volume"] > g.loc[current, "volume"]
            if vol_crossover or sessions_to_expiry <= days_before_expiry:
                rolls.append(RollEvent(
                    date=d,
                    old_expiry=current,
                    new_expiry=second,
                    old_settle=float(g.loc[current, "settle"]),
                    new_settle=float(g.loc[second, "settle"]),
                ))
                current = second

        front_dates.append(d)
        front_settles.append(float(g.loc[current, "settle"]))

    raw_front = pd.Series(front_settles, index=pd.DatetimeIndex(front_dates),
                          name=instrument)

    # Panama back-adjustment: add each roll gap to all history strictly before it.
    adjusted = raw_front.copy()
    for ev in rolls:
        adjusted.loc[adjusted.index < ev.date] += ev.gap

    roll_log = pd.DataFrame(
        [{"date": ev.date, "old_expiry": ev.old_expiry, "new_expiry": ev.new_expiry,
          "old_settle": ev.old_settle, "new_settle": ev.new_settle, "gap": ev.gap}
         for ev in rolls]
    )
    return ContinuousSeries(instrument=instrument, prices=adjusted,
                            raw_front=raw_front, roll_log=roll_log)
