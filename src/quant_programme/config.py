"""Load the master parameter sheet (config/parameters.yaml, Appendix A).

The parameter sheet is the single source of truth. Anything that needs a
parameter still marked null (unmeasured [P0]/[P2] value) must fail loudly
via `require` rather than fall back to an assumption — the handbook
forbids estimated fees anywhere downstream of Phase 0.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "parameters.yaml"


class MissingParameterError(RuntimeError):
    """A required parameter has not been measured/filled in yet."""


@dataclass(frozen=True)
class InstrumentSpec:
    code: str
    name: str
    point_value_thb: float
    tick_size: float
    slippage_ticks_normal: float
    slippage_ticks_roll: float
    commission_per_side_thb: float | None
    initial_margin_thb: float | None
    maintenance_margin_thb: float | None
    enabled: bool = True

    @property
    def tick_value_thb(self) -> float:
        return self.tick_size * self.point_value_thb

    def require_commission(self) -> float:
        if self.commission_per_side_thb is None:
            raise MissingParameterError(
                f"{self.code}: commission_per_side_thb is unset — fill the Phase 0 "
                "cost register in config/parameters.yaml before running cost-aware code."
            )
        return self.commission_per_side_thb

    def require_initial_margin(self) -> float:
        if self.initial_margin_thb is None:
            raise MissingParameterError(
                f"{self.code}: initial_margin_thb is unset — record current TFEX IM "
                "in config/parameters.yaml (Phase 0)."
            )
        return self.initial_margin_thb


@dataclass(frozen=True)
class Config:
    raw: dict[str, Any] = field(repr=False, default_factory=dict)

    # --- convenience accessors -------------------------------------------------
    @property
    def capital(self) -> float:
        return float(self.raw["programme"]["capital_thb"])

    @property
    def weights(self) -> dict[str, float]:
        w = self.raw["strategic_weights"]
        return {k: float(v) for k, v in w.items() if isinstance(v, (int, float))}

    @property
    def overlay(self) -> dict[str, Any]:
        return self.raw["risk_overlay"]

    @property
    def trend(self) -> dict[str, Any]:
        return self.raw["trend_sleeve"]

    @property
    def sleeve_b_capital(self) -> float:
        return self.capital * float(self.raw["strategic_weights"]["sleeve_b_trend"])

    def instruments(self, enabled_only: bool = True) -> dict[str, InstrumentSpec]:
        out: dict[str, InstrumentSpec] = {}
        for code, spec in self.raw["instruments"].items():
            inst = InstrumentSpec(code=code, **spec)
            if enabled_only and not inst.enabled:
                continue
            out[code] = inst
        return out

    def require(self, *path: str) -> Any:
        """Fetch a nested parameter, failing loudly if it is null/missing."""
        node: Any = self.raw
        for key in path:
            if not isinstance(node, dict) or key not in node:
                raise MissingParameterError(f"Parameter {'.'.join(path)} not found in sheet")
            node = node[key]
        if node is None:
            raise MissingParameterError(
                f"Parameter {'.'.join(path)} is unset — fill it in config/parameters.yaml "
                "at the phase indicated in the sheet."
            )
        return node


def load_config(path: str | Path = DEFAULT_CONFIG_PATH) -> Config:
    with open(path, encoding="utf-8") as fh:
        raw = yaml.safe_load(fh)
    weights = raw["strategic_weights"]
    total = sum(v for k, v in weights.items() if isinstance(v, (int, float)))
    if abs(total - 1.0) > 1e-9:
        raise ValueError(f"Strategic weights must sum to 1.0, got {total}")
    return Config(raw=raw)
