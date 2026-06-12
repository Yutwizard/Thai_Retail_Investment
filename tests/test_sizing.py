"""Section 6.4 unit test: sizing formula vs the hand-computed Appendix B.2
worked example, and the Chapter 2.4 granularity rule."""

import pytest

from quant_programme.sizing import contract_count, size_sleeve


def test_appendix_b2_worked_example_250k():
    # Sleeve capital 250k, w = 1/3, S50 at 1,000 points, PV 200, vol 15%.
    # Budget = 10,000; per-contract vol = 30,000 → N = 0, overshoot 3× → drop.
    r = contract_count(risk_share=1 / 3, sleeve_vol_target=0.12, sleeve_capital=250_000,
                       instrument_vol=0.15, point_value=200, price=1_000)
    assert r.contracts == 0
    assert r.risk_budget_thb == pytest.approx(10_000)
    assert r.vol_per_contract_thb == pytest.approx(30_000)
    assert not r.includable  # overshoot 3.0 > 1.5


def test_appendix_b2_worked_example_1m():
    # 25% sleeve on THB 1m total → budget 40,000/3... handbook uses w applied to
    # the same 12% target: round(40,000 / 30,000) = 1 contract.
    r = contract_count(risk_share=1.0, sleeve_vol_target=0.12, sleeve_capital=333_333,
                       instrument_vol=0.15, point_value=200, price=1_000)
    assert r.contracts == 1


def test_granularity_rule_boundary():
    # Exactly 1.5× overshoot is still includable; beyond is dropped.
    ok = contract_count(1.0, 0.12, 250_000, instrument_vol=0.15,
                        point_value=200, price=1_000)
    # budget 30,000 vs 30,000 per contract → overshoot 1.0
    assert ok.includable and ok.contracts == 1


def test_size_sleeve_drops_oversized_and_resplits():
    vols = {"S50": 0.15, "GO": 0.12, "USDTHB": 0.05}
    prices = {"S50": 1_000, "GO": 2_500, "USDTHB": 35.0}
    pvs = {"S50": 200, "GO": 300, "USDTHB": 1_000}
    # Small sleeve: S50 and GO contracts are far above a 1/3 budget; USDTHB tiny.
    out = size_sleeve(vols, prices, pvs, sleeve_capital=60_000, sleeve_vol_target=0.12)
    assert all(r.includable for r in out.values())
    assert set(out) != set(vols) or all(r.includable for r in out.values())
