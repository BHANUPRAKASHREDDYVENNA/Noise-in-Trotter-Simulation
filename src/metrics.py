from __future__ import annotations

import math
from typing import Any


def circuit_metrics(qc: Any) -> dict[str, Any]:
    if any(not hasattr(qc, method) for method in ("count_ops", "depth", "num_qubits")):
        raise TypeError("qc must provide count_ops(), depth(), and num_qubits.")
    ops = qc.count_ops()
    depth = qc.depth()
    num_qubits = qc.num_qubits
    if not isinstance(depth, int) or depth < 0:
        raise ValueError("Circuit depth must be a non-negative integer.")
    if not isinstance(num_qubits, int) or num_qubits <= 0:
        raise ValueError("Circuit qubit count must be positive.")
    two_qubit_names = {"cx", "cz", "ecr", "swap", "rxx", "ryy", "rzz"}
    two_qubit_count = sum(
        int(count) for gate, count in ops.items() if str(gate).lower() in two_qubit_names
    )
    return {
        "depth": depth,
        "physical_qubits": num_qubits,
        "total_ops": int(sum(ops.values())),
        "two_qubit_gate_count": int(two_qubit_count),
        "swap_count": int(ops.get("swap", 0)),
        "operations": dict(ops),
    }


def add_runtime(metrics: dict[str, Any], runtime_seconds: float) -> dict[str, Any]:
    if not isinstance(metrics, dict):
        raise TypeError("metrics must be a dictionary.")
    runtime_seconds = float(runtime_seconds)
    if not math.isfinite(runtime_seconds) or runtime_seconds < 0:
        raise ValueError("runtime_seconds must be finite and non-negative.")
    out = dict(metrics)
    out["runtime_seconds"] = runtime_seconds
    return out


def compute_metric_summary(data: Any) -> dict[str, Any]:
    if hasattr(data, "count_ops"):
        return circuit_metrics(data)
    if isinstance(data, dict):
        return dict(data)
    raise TypeError("Unsupported metric input.")
