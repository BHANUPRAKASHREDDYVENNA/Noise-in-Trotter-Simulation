from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from src.online_ab import embed_logical_state, run_source_ab, validate_layout
from src.validation import ValidationError


def test_source_ab_uses_real_processor_definitions():
    frame = run_source_ab()
    assert list(frame["processor"]) == ["A", "B"]
    assert list(frame["physical_qubits"]) == [5.0, 7.0]
    assert list(frame["processor_name"]) == ["processor_A", "processor_B"]
    assert set(frame["processor_source"]) == {"source_document"}
    assert set(frame["logical_qubits"]) == {3.0}
    assert set(frame["seed"]) == {2026.0}
    assert list(frame["compilation_baseline"]) == [
        "deterministic reference routing",
        "contemporary compilation baseline",
    ]


def test_source_ab_uses_identical_controlled_noise():
    frame = run_source_ab()
    assert frame["p1"].nunique() == 1
    assert frame["p2"].nunique() == 1
    assert frame["readout_error"].nunique() == 1


def test_source_ab_routing_matches_source_graphs():
    frame = run_source_ab().set_index("processor")
    assert frame.loc["A", "swap_count"] == 0.0
    assert frame.loc["B", "swap_count"] == 8.0
    assert frame.loc["A", "two_qubit_gate_count"] == 4.0
    assert frame.loc["B", "two_qubit_gate_count"] == 28.0


def test_source_ab_is_reproducible_with_one_common_seed():
    first = run_source_ab()
    second = run_source_ab()
    pd.testing.assert_frame_equal(first, second)


def test_embedding_preserves_state_norm_and_rejects_bad_layout():
    logical = np.array([1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0], dtype=complex)
    embedded = embed_logical_state(logical, 3, 7, (0, 1, 2))
    assert np.isclose(np.linalg.norm(embedded), 1.0)
    with pytest.raises(ValidationError):
        validate_layout((0, 0, 2), 3, 7)
