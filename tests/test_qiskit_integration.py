from __future__ import annotations

import pytest
from qiskit import QuantumCircuit

from src.metrics import add_runtime, circuit_metrics
from src.routing import transpile_for_processor


PROCESSOR = {
    "name": "test_line_3q",
    "num_qubits": 3,
    "coupling_map": [[0, 1], [1, 2]],
    "basis_gates": ["rz", "sx", "x", "cx"],
}


def test_transpile_adapter_and_metrics():
    circuit = QuantumCircuit(3)
    circuit.h(0)
    circuit.cx(0, 2)

    compiled = transpile_for_processor(
        circuit,
        PROCESSOR,
        optimization_level=0,
        seed_transpiler=2026,
    )
    metrics = circuit_metrics(compiled)

    assert metrics["physical_qubits"] == 3
    assert metrics["depth"] > 0
    assert metrics["two_qubit_gate_count"] >= 1
    assert metrics["swap_count"] >= 0


def test_transpile_adapter_rejects_invalid_controls():
    circuit = QuantumCircuit(2)
    with pytest.raises(ValueError):
        transpile_for_processor(circuit, PROCESSOR, optimization_level=4)
    with pytest.raises(ValueError):
        transpile_for_processor(circuit, PROCESSOR, seed_transpiler=True)


def test_runtime_metric_validation():
    metrics = {"depth": 3}
    assert add_runtime(metrics, 0.25)["runtime_seconds"] == 0.25
    with pytest.raises(ValueError):
        add_runtime(metrics, -1)
