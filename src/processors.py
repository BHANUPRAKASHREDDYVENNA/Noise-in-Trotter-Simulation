from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_processor(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_processor_definition(processor: dict[str, Any], label: str) -> None:
    required = ["name", "num_qubits", "coupling_map", "basis_gates"]
    missing = [k for k in required if k not in processor]
    if missing:
        raise ValueError(f"{label} is missing required fields: {missing}")
    if processor.get("num_qubits") in (None, 0):
        raise ValueError(f"{label} still contains placeholder num_qubits.")
    if not processor.get("coupling_map"):
        raise ValueError(f"{label} still contains a placeholder coupling_map.")
