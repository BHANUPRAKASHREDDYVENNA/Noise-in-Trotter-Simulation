from __future__ import annotations

import pytest

from src.processors import interaction_swap_count, shortest_path
from src.validation import (
    ValidationError,
    probability,
    validate_processor_mapping,
    validate_statevector_size,
    validate_trotter_parameters,
)


def test_invalid_probability_range_is_rejected():
    with pytest.raises(ValidationError):
        probability("p", 1.1)


def test_invalid_processor_edge_is_rejected():
    with pytest.raises(ValidationError):
        validate_processor_mapping(((0, 1), (1, 3)), 3)


def test_duplicate_processor_edge_is_rejected():
    with pytest.raises(ValidationError):
        validate_processor_mapping(((0, 1), (1, 0)), 2)


def test_statevector_memory_guard():
    with pytest.raises(ValidationError):
        validate_statevector_size(30, max_bytes=1024)


def test_trotter_trajectory_limit():
    with pytest.raises(ValidationError):
        validate_trotter_parameters(
            n_qubits=3,
            steps=1,
            total_time=0.1,
            coupling=1.0,
            field=0.7,
            trajectories=1_000_001,
        )


def test_negative_total_time_is_rejected():
    with pytest.raises(ValidationError):
        validate_trotter_parameters(
            n_qubits=3,
            steps=1,
            total_time=-0.1,
            coupling=1.0,
            field=0.7,
        )


def test_shortest_path_and_swap_count():
    coupling = ((0, 1), (1, 2), (2, 3))
    assert shortest_path(coupling, 4, 0, 3) == (0, 1, 2, 3)
    assert interaction_swap_count(coupling, 4, 0, 3) == 2
    assert interaction_swap_count(coupling, 4, 0, 3, restore_layout=True) == 4


def test_unreachable_path_is_rejected():
    with pytest.raises(ValidationError):
        shortest_path(((0, 1), (2, 3)), 4, 0, 3)
