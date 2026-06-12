"""Performance metrics (Appendix B.5).

Excess return = portfolio return − THOR. Sharpe = annualised excess /
annualised vol. Max drawdown on daily NAV; hit rate = % profitable months.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

TRADING_DAYS = 252


def annualised_return(daily_returns: pd.Series) -> float:
    cum = (1 + daily_returns).prod()
    years = len(daily_returns) / TRADING_DAYS
    return cum ** (1 / years) - 1 if years > 0 else 0.0


def annualised_vol(daily_returns: pd.Series) -> float:
    return float(daily_returns.std() * np.sqrt(TRADING_DAYS))


def sharpe_vs_benchmark(daily_returns: pd.Series, benchmark_daily: pd.Series) -> float:
    """Sharpe of excess returns over the cash benchmark (THOR)."""
    excess = (daily_returns - benchmark_daily.reindex(daily_returns.index).fillna(0.0)).dropna()
    vol = annualised_vol(excess)
    return float(excess.mean() * TRADING_DAYS / vol) if vol > 0 else 0.0


def max_drawdown(nav: pd.Series) -> float:
    """Max drawdown on daily NAV, returned as a negative fraction."""
    hwm = nav.cummax()
    return float((nav / hwm - 1).min())


def hit_rate(daily_returns: pd.Series) -> float:
    monthly = (1 + daily_returns).groupby(daily_returns.index.to_period("M")).prod() - 1
    return float((monthly > 0).mean()) if len(monthly) else 0.0


def summary(daily_returns: pd.Series, benchmark_daily: pd.Series,
            cost_drag: float | None = None) -> dict[str, float]:
    nav = (1 + daily_returns).cumprod()
    out = {
        "cagr": annualised_return(daily_returns),
        "vol": annualised_vol(daily_returns),
        "sharpe_vs_thor": sharpe_vs_benchmark(daily_returns, benchmark_daily),
        "max_drawdown": max_drawdown(nav),
        "hit_rate": hit_rate(daily_returns),
    }
    if cost_drag is not None:
        out["cost_drag_pa"] = cost_drag
    return out
