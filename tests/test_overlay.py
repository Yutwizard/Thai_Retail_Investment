"""Risk overlay tests (Ch.2.2 / B.3): vol-target multiplier split and the
−15%/−7.5% circuit breaker must match the specification exactly."""

import numpy as np
import pandas as pd

from quant_programme.portfolio.overlay import circuit_breaker, split_multiplier


def test_split_multiplier_trend_first():
    # m above the 0.7 threshold: only the trend sleeve is scaled.
    trend, beta = split_multiplier(0.85, beta_threshold=0.70)
    assert trend == 0.85 and beta == 1.0


def test_split_multiplier_beta_below_threshold():
    trend, beta = split_multiplier(0.35, beta_threshold=0.70)
    assert trend == 0.35
    assert beta == 0.5  # 0.35 / 0.70


def test_split_multiplier_no_scaling_at_or_above_one():
    assert split_multiplier(1.0) == (1.0, 1.0)


def test_circuit_breaker_trigger_and_restore():
    # NAV: rises to 100, falls 20% (through −15% trigger), recovers inside −7.5%.
    nav = pd.Series(
        [100, 100, 90, 84, 80, 85, 90, 93, 95, 100],
        index=pd.bdate_range("2024-01-01", periods=10),
        dtype=float,
    )
    factor, events = circuit_breaker(nav, trigger=-0.15, restore=-0.075, cut_fraction=0.5)
    assert [e.action for e in events] == ["trigger", "restore"]
    # tripped at 84 (−16%), restored at 93 (−7%)
    assert events[0].drawdown <= -0.15
    assert events[1].drawdown >= -0.075
    tripped_days = factor[factor == 0.5].index
    assert nav.loc[tripped_days].min() == 80
    # full exposure restored after recovery
    assert factor.iloc[-1] == 1.0


def test_circuit_breaker_never_fires_in_calm_market():
    nav = pd.Series(np.linspace(100, 120, 50), index=pd.bdate_range("2024-01-01", periods=50))
    factor, events = circuit_breaker(nav)
    assert events == []
    assert (factor == 1.0).all()
