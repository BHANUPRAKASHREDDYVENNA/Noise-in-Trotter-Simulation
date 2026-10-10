from __future__ import annotations

import pytest

from src.metrics import add_runtime, circuit_metrics


class FakeCircuit:
    num_qubits = 3

    def __init__(self, operations: dict[str, int], depth: int = 2):
        self._operations = operations
        self._depth = depth

    def count_ops(self):
        return self._operations

    def depth(self):
        return self._depth


def test_circuit_metrics_rejects_invalid_operation_counts():
    with pytest.raises(ValueError):
        circuit_metrics(FakeCircuit({"cx": -1}))


def test_circuit_metrics_counts_two_qubit_operations():
    metrics = circuit_metrics(FakeCircuit({"rz": 2, "cx": 3, "swap": 1}))
    assert metrics["total_ops"] == 6
    assert metrics["two_qubit_gate_count"] == 4
    assert metrics["swap_count"] == 1


def test_runtime_metric_rejects_nan():
    with pytest.raises(ValueError):
        add_runtime({}, float("nan"))
