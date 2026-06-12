"""Data ingestion interfaces (Phase 1, Ch.5.1).

This repo deliberately contains no scraping code. Ingestion is an adapter
boundary: the existing Playwright TFEX scraper and BOT API integration plug
in by implementing `SeriesSource`, or simply by dropping files into
data/raw/ in the documented schema (see schemas.py) for `FileSource`.

Required series (Ch.5.1):
  - per-expiry daily futures settlements for S50 / GO / USDTHB
  - THOR / T-bill yield (cash benchmark)
  - SET50 TRI, global equity TRI (USD + THB-converted)
  - USD/THB spot
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

import pandas as pd

from .schemas import validate_futures_frame, validate_series_frame

DEFAULT_RAW_DIR = Path(__file__).resolve().parents[3] / "data" / "raw"


class SeriesSource(Protocol):
    """Adapter protocol for any upstream data provider."""

    def futures_settlements(self, instrument: str) -> pd.DataFrame:
        """All listed expiries: columns [date, expiry, settle, volume, open_interest]."""
        ...

    def benchmark_series(self, name: str) -> pd.Series:
        """Daily series indexed by date (e.g. 'THOR', 'SET50_TRI', 'USDTHB_SPOT')."""
        ...


class FileSource:
    """Reads CSV/parquet drops from data/raw/.

    Layout:
        data/raw/futures/<INSTRUMENT>.csv|parquet   (long format, all expiries)
        data/raw/benchmarks/<NAME>.csv|parquet      (columns: date, value)
    """

    def __init__(self, root: str | Path = DEFAULT_RAW_DIR) -> None:
        self.root = Path(root)

    def _read(self, path_no_ext: Path) -> pd.DataFrame:
        for ext, reader in ((".parquet", pd.read_parquet), (".csv", pd.read_csv)):
            p = path_no_ext.with_suffix(ext)
            if p.exists():
                return reader(p)
        raise FileNotFoundError(
            f"No {path_no_ext}.parquet or .csv found — drop the export from the "
            "upstream scraper there, or wire a custom SeriesSource adapter."
        )

    def futures_settlements(self, instrument: str) -> pd.DataFrame:
        df = self._read(self.root / "futures" / instrument)
        return validate_futures_frame(df, instrument)

    def benchmark_series(self, name: str) -> pd.Series:
        df = self._read(self.root / "benchmarks" / name)
        return validate_series_frame(df, name)
