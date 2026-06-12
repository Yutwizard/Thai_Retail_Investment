"""Expected input schemas for raw data drops / adapters."""

from __future__ import annotations

import pandas as pd

FUTURES_COLUMNS = ["date", "expiry", "settle", "volume", "open_interest"]


def validate_futures_frame(df: pd.DataFrame, instrument: str) -> pd.DataFrame:
    missing = [c for c in FUTURES_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"{instrument}: futures frame missing columns {missing}; "
                         f"expected {FUTURES_COLUMNS}")
    out = df.copy()
    out["date"] = pd.to_datetime(out["date"])
    out["expiry"] = pd.to_datetime(out["expiry"])
    out = out.sort_values(["date", "expiry"]).reset_index(drop=True)
    if out.duplicated(["date", "expiry"]).any():
        raise ValueError(f"{instrument}: duplicate (date, expiry) rows in raw data")
    return out


def validate_series_frame(df: pd.DataFrame, name: str) -> pd.Series:
    if not {"date", "value"}.issubset(df.columns):
        raise ValueError(f"{name}: benchmark frame must have columns [date, value]")
    s = df.set_index(pd.to_datetime(df["date"]))["value"].astype(float).sort_index()
    s.name = name
    return s
