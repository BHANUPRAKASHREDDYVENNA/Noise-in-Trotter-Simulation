"""S3 problem helpers for the guide-derived Phase-1 demonstrator."""
from __future__ import annotations

from pathlib import Path
import json
from typing import Any

from .practice_s3 import logical_trotter_circuit


def load_settings(path: str | Path = "data/guide_settings.json") -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as f:
        return json.load(f)


def build_s3_logical_workload(settings: dict[str, Any]):
    cfg = settings["trotter_demo"]
    return logical_trotter_circuit(
        cfg["trotter_steps"],
        cfg["total_time"],
        cfg["J"],
        cfg["h"],
    )
