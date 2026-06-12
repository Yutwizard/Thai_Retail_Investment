"""Per-instrument constant-risk contract sizing (Ch.6.1, Appendix B.2)
and the Chapter 2.4 granularity rule.

N_i = round( (w_i × σ_target × C_B) / (σ_i × PV_i × P_i) )

where w_i is the instrument's risk-budget share, σ_target the sleeve vol
target (12%), C_B sleeve capital, σ_i instrument annualised vol, PV_i point
value (THB per point), P_i current price in points.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SizingResult:
    contracts: int
    risk_budget_thb: float          # w_i × σ_target × C_B (annualised vol budget)
    vol_per_contract_thb: float     # σ_i × PV_i × P_i
    includable: bool                # passes the granularity rule
    overshoot: float                # vol of 1 contract / risk budget


def contract_count(risk_share: float, sleeve_vol_target: float, sleeve_capital: float,
                   instrument_vol: float, point_value: float, price: float,
                   granularity_max_overshoot: float = 1.5) -> SizingResult:
    """Worked example (B.2): sleeve capital 250k, w=1/3, S50 at 1,000 pts,
    PV 200, vol 15% → budget 10,000 vs 30,000 per contract → N = 0."""
    budget = risk_share * sleeve_vol_target * sleeve_capital
    per_contract = instrument_vol * point_value * price
    n = round(budget / per_contract)
    overshoot = per_contract / budget if budget > 0 else float("inf")
    # Granularity rule (Ch.2.4): include only if one contract is no more than
    # 1.5× the per-instrument risk budget; if a single contract overshoots by
    # more than 50%, drop the instrument rather than run it oversized.
    includable = overshoot <= granularity_max_overshoot
    return SizingResult(contracts=int(n), risk_budget_thb=budget,
                        vol_per_contract_thb=per_contract,
                        includable=includable, overshoot=overshoot)


def size_sleeve(instrument_vols: dict[str, float], prices: dict[str, float],
                point_values: dict[str, float], sleeve_capital: float,
                sleeve_vol_target: float = 0.12,
                granularity_max_overshoot: float = 1.5) -> dict[str, SizingResult]:
    """Equal risk share across included instruments. Instruments failing the
    granularity rule are dropped and the budget re-split among the rest,
    matching the Ch.2.4 capital-scaling variants."""
    codes = list(instrument_vols)
    while codes:
        share = 1.0 / len(codes)
        results = {
            c: contract_count(share, sleeve_vol_target, sleeve_capital,
                              instrument_vols[c], point_values[c], prices[c],
                              granularity_max_overshoot)
            for c in codes
        }
        excluded = [c for c, r in results.items() if not r.includable]
        if not excluded:
            return results
        # Drop the worst offender and re-split.
        codes.remove(max(excluded, key=lambda c: results[c].overshoot))
    return {}
