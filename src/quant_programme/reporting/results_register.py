"""Results register (Ch.6.4): every backtest run writes a config hash and a
results row, so the sensitivity grid and any future re-run are reproducible
and comparable. The register is an append-only CSV under results/.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

DEFAULT_REGISTER = Path(__file__).resolve().parents[3] / "results" / "register.csv"


def config_hash(params: dict[str, Any]) -> str:
    blob = json.dumps(params, sort_keys=True, default=str).encode()
    return hashlib.sha256(blob).hexdigest()[:12]


def record_run(params: dict[str, Any], metrics: dict[str, float],
               register_path: str | Path = DEFAULT_REGISTER) -> str:
    path = Path(register_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    h = config_hash(params)
    row = {
        "run_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "config_hash": h,
        "params": json.dumps(params, sort_keys=True, default=str),
        **metrics,
    }
    df = pd.DataFrame([row])
    df.to_csv(path, mode="a", header=not path.exists(), index=False)
    return h
