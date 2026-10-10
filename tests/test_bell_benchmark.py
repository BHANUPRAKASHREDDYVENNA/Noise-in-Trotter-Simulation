from __future__ import annotations

import numpy as np
import pytest

from src.bell_benchmark import (
    ProcessorModel,
    apply_readout_error,
    bell_correlations,
    bell_state,
    benchmark_bell_processor,
    postselect_bell_z_counts,
    proportion_standard_error,
)
from src.validation import ValidationError


def test_bell_state_correlations():
    corr = bell_correlations(bell_state())
    assert np.isclose(corr["XX"], 1.0)
    assert np.isclose(corr["YY"], -1.0)
    assert np.isclose(corr["ZZ"], 1.0)


def test_standard_error():
    assert np.isclose(
        proportion_standard_error(0.92, 2048),
        np.sqrt(0.92 * 0.08 / 2048),
    )


def test_readout_error_changes_measurement_distribution():
    noisy = apply_readout_error(
        {"00": 1.0, "01": 0.0, "10": 0.0, "11": 0.0},
        0.1,
    )
    assert noisy["00"] < 1.0
    assert np.isclose(sum(noisy.values()), 1.0)


def test_readout_error_rejects_unnormalized_input():
    with pytest.raises(ValidationError):
        apply_readout_error(
            {"00": 0.5, "01": 0.0, "10": 0.0, "11": 0.0},
            0.1,
        )


def test_postselection_rejects_negative_counts():
    with pytest.raises(ValidationError):
        postselect_bell_z_counts({"00": -1, "11": 2})


def test_processor_validation_rejects_bad_qubit_count():
    with pytest.raises(ValidationError):
        ProcessorModel("bad", 1, ((0, 1),), 0.01, 0.01, 0.01)


def test_processor_ports_drive_routing_metric():
    processor = ProcessorModel(
        "line4",
        4,
        ((0, 1), (1, 2), (2, 3)),
        0.01,
        0.01,
        0.01,
        ports=(0, 3),
    )
    result = benchmark_bell_processor(processor, shots=128, seed=11)
    assert result["swap_overhead"] == 2.0
    assert result["two_qubit_gates"] == 7.0
