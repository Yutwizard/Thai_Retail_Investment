"""Section 6.4 unit test: the cost engine charges exactly 2 sides per
roll-log entry, and refuses to run on unmeasured Phase 0 fees."""

import pandas as pd
import pytest

from quant_programme.config import InstrumentSpec, MissingParameterError
from quant_programme.costs import charge_rolls, charge_signal_trade, cost_drag_pa, side_cost


def _spec(commission=45.0) -> InstrumentSpec:
    return InstrumentSpec(
        code="S50", name="SET50 Index Futures", point_value_thb=200, tick_size=0.1,
        slippage_ticks_normal=1, slippage_ticks_roll=2,
        commission_per_side_thb=commission,
        initial_margin_thb=None, maintenance_margin_thb=None,
    )


def test_missing_commission_raises():
    with pytest.raises(MissingParameterError):
        side_cost(_spec(commission=None), contracts=1)


def test_side_cost_components():
    # commission 45 + 1 tick slippage (0.1 × 200 = 20) = 65 per contract per side
    assert side_cost(_spec(), contracts=1) == 65.0
    assert side_cost(_spec(), contracts=3) == 195.0


def test_roll_charged_exactly_two_sides_per_entry():
    dates = pd.bdate_range("2020-01-01", periods=100)
    positions = pd.Series(2, index=dates)
    roll_log = pd.DataFrame({
        "date": [dates[30], dates[60]],
        "old_expiry": [dates[40], dates[70]],
        "new_expiry": [dates[90], dates[99]],
        "old_settle": [1000.0, 1010.0],
        "new_settle": [1002.0, 1012.0],
        "gap": [2.0, 2.0],
    })
    costs = charge_rolls(_spec(), roll_log, positions)
    assert len(costs) == 2
    for c in costs:
        assert c.sides == 2
        assert c.kind == "roll"
        # 2 sides × 2 contracts × (45 + 2 ticks × 20) = 2 × 2 × 85 = 340
        assert c.cost_thb == 340.0


def test_roll_not_charged_when_flat():
    dates = pd.bdate_range("2020-01-01", periods=10)
    positions = pd.Series(0, index=dates)
    roll_log = pd.DataFrame({"date": [dates[5]], "old_expiry": [dates[6]],
                             "new_expiry": [dates[9]], "old_settle": [1.0],
                             "new_settle": [1.0], "gap": [0.0]})
    assert charge_rolls(_spec(), roll_log, positions) == []


def test_signal_trade_zero_delta_is_free():
    assert charge_signal_trade(_spec(), pd.Timestamp("2020-01-01"), 0) is None


def test_cost_drag_annualisation():
    c = charge_signal_trade(_spec(), pd.Timestamp("2020-01-01"), 1)
    drag = cost_drag_pa([c], sleeve_capital=150_000, years=1.0)
    assert drag == pytest.approx(65.0 / 150_000)
