"""Master parameter sheet loading and the fail-loud rule for unmeasured values."""

import pytest

from quant_programme.config import MissingParameterError, load_config


def test_sheet_loads_and_weights_sum_to_one():
    cfg = load_config()
    assert cfg.capital == 600_000
    assert sum(cfg.weights.values()) == pytest.approx(1.0)
    assert cfg.sleeve_b_capital == pytest.approx(150_000)


def test_three_market_sleeve_enabled_at_600k():
    cfg = load_config()
    assert set(cfg.instruments()) == {"S50", "GO", "USDTHB"}


def test_unmeasured_p0_values_fail_loudly():
    cfg = load_config()
    with pytest.raises(MissingParameterError):
        cfg.instruments()["S50"].require_commission()
    with pytest.raises(MissingParameterError):
        cfg.require("margin_model", "broker_collateral_policy")


def test_overlay_parameters_match_handbook():
    cfg = load_config()
    assert cfg.overlay["portfolio_vol_target"] == 0.10
    assert cfg.overlay["circuit_breaker_drawdown"] == -0.15
    assert cfg.overlay["circuit_breaker_restore"] == -0.075
    assert cfg.trend["sleeve_vol_target"] == 0.12
    assert cfg.trend["signal_lookback_days"] == 252
