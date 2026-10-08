from __future__ import annotations

from typing import Any


def circuit_metrics(qc: Any) -> dict[str, Any]:
    ops = qc.count_ops()
    two_qubit_names = {"cx", "cz", "ecr", "swap", "rxx", "ryy", "rzz"}
    return {
        "depth": qc.depth(),
        "physical_qubits": qc.num_qubits,
        "total_ops": int(sum(ops.values())),
        "two_qubit_gate_count": int(sum(n for g, n in ops.items() if g.lower() in two_qubit_names)),
        "swap_count": int(ops.get("swap", 0)),
        "operations": dict(ops),
    }


def add_runtime(metrics: dict[str, Any], runtime_seconds: float) -> dict[str, Any]:
    out = dict(metrics)
    out["runtime_seconds"] = float(runtime_seconds)
    return out


def compute_metric_summary(data: Any) -> dict[str, Any]:
    """Return a small summary for a circuit-like object or result mapping."""
    if hasattr(data, "count_ops"):
        return circuit_metrics(data)
    if isinstance(data, dict):
        return dict(data)
    raise TypeError("Unsupported metric input")
