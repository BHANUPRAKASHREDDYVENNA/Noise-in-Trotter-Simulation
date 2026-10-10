from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.practice_s3 import (
    PracticeProcessor,
    benchmark_processor,
    compile_practice,
    ideal_exact_state,
    logical_trotter_circuit,
)


def test_logical_trotter_builds():
    gates = logical_trotter_circuit(4, 0.8, 1.0, 0.7)
    assert len(gates) == 8
    assert all(g.name in {"rzz", "rx"} for g in gates)


def test_line_processor_adds_routing():
    gates = logical_trotter_circuit(2, 0.4, 1.0, 0.7)
    a = PracticeProcessor("A", 3, ((0, 1), (0, 2), (1, 2)), 0, 0, 0)
    b = PracticeProcessor("B", 3, ((0, 1), (1, 2)), 0, 0, 0)
    ca = compile_practice(gates, a)
    cb = compile_practice(gates, b)
    assert len(cb) > len(ca)
    routing_a = sum(g.role == "routing" for g in ca)
    routing_b = sum(g.role == "routing" for g in cb)
    assert routing_b > routing_a
    assert routing_b % 3 == 0


def test_exact_state_is_normalized():
    state = ideal_exact_state(3, 0.8, 1.0, 0.7)
    assert np.isclose(np.linalg.norm(state), 1.0)


def test_practice_benchmark_is_deterministic():
    cfg = json.loads((ROOT / "data" / "practice_config.json").read_text())
    s = cfg["system"]
    logical = logical_trotter_circuit(s["trotter_steps"], s["total_time"], s["J"], s["h"])
    exact = ideal_exact_state(s["n_qubits"], s["total_time"], s["J"], s["h"])
    p = cfg["processors"]["A"]
    processor = PracticeProcessor(
        p["name"],
        s["n_qubits"],
        tuple(tuple(edge) for edge in p["coupling_map"]),
        p["p1"],
        p["p2"],
        p["readout_error"],
    )
    r1 = benchmark_processor(processor, logical, exact, s["n_qubits"], 50, 123)
    r2 = benchmark_processor(processor, logical, exact, s["n_qubits"], 50, 123)
    assert r1 == r2


def test_routing_preserves_ideal_fidelity_reference():
    logical = logical_trotter_circuit(2, 0.4, 1.0, 0.7)
    exact = ideal_exact_state(3, 0.4, 1.0, 0.7)
    processor_a = PracticeProcessor(
        "fully_connected", 3, ((0, 1), (0, 2), (1, 2)), 0.0, 0.0, 0.0
    )
    processor_b = PracticeProcessor(
        "line", 3, ((0, 1), (1, 2)), 0.0, 0.0, 0.0
    )
    metrics_a = benchmark_processor(processor_a, logical, exact, 3, 10, 5)
    metrics_b = benchmark_processor(processor_b, logical, exact, 3, 10, 5)
    assert np.isclose(metrics_a["mean_fidelity"], metrics_b["mean_fidelity"])


def test_config_is_not_claimed_official():
    spec = json.loads((ROOT / "data" / "guide_settings.json").read_text())
    assert spec["status"] == "GUIDE_DERIVED_DEMONSTRATOR"
