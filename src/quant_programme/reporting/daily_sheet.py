"""Daily Sheet (Ch.8.1): the output of the automated daily cycle, reviewed
by a human in ~5 minutes. Emits current vs target positions, any action
required tomorrow, margin utilisation vs buffer, and circuit-breaker distance.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass
class ActionItem:
    instrument: str
    action: str               # e.g. "BUY 1", "SELL 2", "ROLL"
    reason: str               # "rebalance" | "signal flip" | "vol band" | "roll T-5"


@dataclass
class DailySheet:
    as_of: date
    positions_current: dict[str, int]
    positions_target: dict[str, int]
    overlay_multiplier: float
    drawdown: float
    breaker_distance: float           # drawdown − trigger; negative means tripped
    margin_utilisation: float         # required / cash buffer
    validation_green: bool
    actions: list[ActionItem] = field(default_factory=list)

    def render(self) -> str:
        lines = [
            f"DAILY SHEET — {self.as_of.isoformat()}",
            f"Validation suite: {'GREEN' if self.validation_green else 'RED — DO NOT TRADE'}",
            f"Overlay multiplier m: {self.overlay_multiplier:.2f}",
            f"Drawdown vs HWM: {self.drawdown:.1%}  "
            f"(distance to −15% breaker: {self.breaker_distance:.1%})",
            f"Margin utilisation vs buffer: {self.margin_utilisation:.0%}"
            + ("  ⚠ > 60% limit" if self.margin_utilisation > 0.60 else ""),
            "",
            "Positions (current → target):",
        ]
        for code in sorted(set(self.positions_current) | set(self.positions_target)):
            cur = self.positions_current.get(code, 0)
            tgt = self.positions_target.get(code, 0)
            flag = "" if cur == tgt else "  ← ACTION"
            lines.append(f"  {code}: {cur} → {tgt}{flag}")
        lines.append("")
        if self.actions:
            lines.append("Action items for tomorrow (require sign-off):")
            lines += [f"  [{a.instrument}] {a.action} — {a.reason}" for a in self.actions]
        else:
            lines.append("No action required.")
        return "\n".join(lines)
