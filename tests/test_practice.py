from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.practice_s3 import (  # noqa: E402
    PracticeProcessor,
    benchmark_processor,
    compile_practice,
    ideal_exact_state,
    logical_trotter_circuit,
)
from src.validation import ValidationError  # noqa: E402


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


def test_invalid_seed_is_rejected():
    gates = logical_trotter_circuit(1, 0.2, 1.0, 0.7)
    exact = ideal_exact_state(3, 0.2, 1.0, 0.7)
    processor = PracticeProcessor("A", 3, ((0, 1), (1, 2)), 0, 0, 0)
    with pytest.raises(ValidationError):
        benchmark_processor(processor, gates, exact, 3, 1, -1)


def test_non_gate_input_is_rejected():
    processor = PracticeProcessor("A", 3, ((0, 1), (1, 2)), 0, 0, 0)
    with pytest.raises(ValidationError):
        compile_practice([object()], processor)


def test_exact_state_is_normalized():
    state = ideal_exact_state(3, 0.8, 1.0, 0.7)
    assert np.isclose(np.linalg.norm(state), 1.0)


def test_practice_benchmark_is_deterministic():
    first = run_source_ab()
    second = run_source_ab()
    pd.testing.assert_frame_equal(first, second)


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
