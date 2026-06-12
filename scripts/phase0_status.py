#!/usr/bin/env python3
"""Phase 0 status and stage-gate readiness.

Reads config/parameters.yaml and reports which [P0] measurements are still
unfilled, checks the Phase 0 exit criteria that are machine-checkable, and
(with --buffer) sizes the cash buffer against peak stressed margin per
handbook §3.4 to decide the 20/5 vs 15/10 ballast split.

Usage:
    python scripts/phase0_status.py
    python scripts/phase0_status.py --buffer --contracts S50=2 GO=1 USDTHB=3 \
        --daily-vol-thb 4000
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from quant_programme.config import Config, MissingParameterError, load_config  # noqa: E402

OK, MISSING = "✔", "✘"


def p0_items(cfg: Config) -> list[tuple[str, bool, str]]:
    """(label, filled?, where to record it)"""
    items: list[tuple[str, bool, str]] = []
    for code, inst in cfg.instruments(enabled_only=False).items():
        items.append((f"{code} commission per side", inst.commission_per_side_thb is not None,
                      f"instruments.{code}.commission_per_side_thb"))
        items.append((f"{code} initial margin", inst.initial_margin_thb is not None,
                      f"instruments.{code}.initial_margin_thb"))
        items.append((f"{code} maintenance margin", inst.maintenance_margin_thb is not None,
                      f"instruments.{code}.maintenance_margin_thb"))
    raw = cfg.raw
    items += [
        ("SET commission rate (incl. VAT)", raw["costs"]["set_commission_rate"] is not None,
         "costs.set_commission_rate"),
        ("Broker margin-collateral policy (in writing)",
         raw["margin_model"]["broker_collateral_policy"] is not None,
         "margin_model.broker_collateral_policy"),
        ("Feeder fund TERs", raw["sleeve_a"]["feeder_fund_ter"] is not None,
         "sleeve_a.feeder_fund_ter"),
        ("Broker selected", raw["phase0_register"]["broker"] is not None,
         "phase0_register.broker"),
        ("DR shortlist (4–6 names)", len(raw["phase0_register"]["dr_shortlist"]) >= 4,
         "phase0_register.dr_shortlist"),
        ("RMF/SSF/ThaiESG providers",
         len(raw["phase0_register"]["rmf_ssf_thaiesg_providers"]) > 0,
         "phase0_register.rmf_ssf_thaiesg_providers"),
        ("MMF selected (with cut-off)", raw["phase0_register"]["mmf_fund"] is not None,
         "phase0_register.mmf_fund"),
        ("Bond fund selected", raw["phase0_register"]["bond_fund"] is not None,
         "phase0_register.bond_fund"),
    ]
    return items


def buffer_sizing(cfg: Config, contracts: dict[str, int], daily_vol_thb: float) -> None:
    mm = cfg.raw["margin_model"]
    stressed = float(mm["stressed_im_multiplier"])
    vm_days = int(mm["adverse_vm_days"])
    vm_mult = float(mm["adverse_vm_vol_multiplier"])

    im_total = 0.0
    print("\nPeak stressed margin (§3.4):")
    for code, n in contracts.items():
        spec = cfg.instruments(enabled_only=False)[code]
        im = spec.require_initial_margin()
        line = n * im * stressed
        im_total += line
        print(f"  {code}: {n} × {im:,.0f} × {stressed} = THB {line:,.0f}")
    vm = vm_days * vm_mult * daily_vol_thb
    required = im_total + vm
    print(f"  Adverse VM: {vm_days} days × {vm_mult}σ × {daily_vol_thb:,.0f} = THB {vm:,.0f}")
    print(f"  TOTAL required: THB {required:,.0f}")

    cash_buffer = cfg.capital * cfg.weights["sleeve_d_cash"]
    print(f"\nCash buffer at current split: THB {cash_buffer:,.0f} "
          f"({cfg.weights['sleeve_d_cash']:.0%} of {cfg.capital:,.0f})")
    if required <= cash_buffer:
        print("→ PASS: buffer covers peak stress. Keep current ballast split; "
              "pre-authorise same-day MMF redemption as the second line if cash-only.")
    else:
        print(f"→ SHORTFALL of THB {required - cash_buffer:,.0f}: shift ballast split "
              "to 15/10 per §3.4 rather than risk forced liquidation of the beta sleeve.")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--buffer", action="store_true", help="run §3.4 buffer sizing")
    ap.add_argument("--contracts", nargs="*", default=[],
                    help="max sleeve positions, e.g. S50=2 GO=1 USDTHB=3")
    ap.add_argument("--daily-vol-thb", type=float, default=None,
                    help="portfolio daily vol in THB for the adverse-VM term")
    args = ap.parse_args()

    cfg = load_config()
    items = p0_items(cfg)
    filled = sum(1 for _, ok, _ in items if ok)

    print(f"PHASE 0 STATUS — {filled}/{len(items)} measured inputs recorded\n")
    for label, ok, where in items:
        mark = OK if ok else MISSING
        print(f"  {mark} {label}" + ("" if ok else f"   → {where}"))

    print("\nManual gate items (see docs/phase_gates.md): accounts funded, "
          "round trips reconciled, written collateral confirmation filed, "
          "first wrapper contributions scheduled.")

    if args.buffer:
        if not args.contracts or args.daily_vol_thb is None:
            ap.error("--buffer requires --contracts and --daily-vol-thb")
        contracts = {k: int(v) for k, v in (c.split("=") for c in args.contracts)}
        try:
            buffer_sizing(cfg, contracts, args.daily_vol_thb)
        except MissingParameterError as exc:
            print(f"\nBuffer sizing blocked: {exc}")
            return 1

    return 0 if filled == len(items) else 1


if __name__ == "__main__":
    raise SystemExit(main())
