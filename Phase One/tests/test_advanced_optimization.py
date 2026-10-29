"""Unit and integration tests for the next-level optimization suite."""

from __future__ import annotations

import numpy as np
import pytest

from src.advanced_optimization import (
    apply_unitary_folding,
    evaluate_layout,
    find_optimal_layout,
    invert_readout_error,
    richardson_extrapolate,
    symmetric_trotter_circuit,
)
from src.processor_d_designer import (
    benchmark_bell_port_correlation,
    compute_graph_metrics,
)
from src.processors import load_processor


def test_optimal_layout_eliminates_processor_b_swaps():
    """Verify that geometry-aware layout finder finds a 0-SWAP embedding for Processor B."""
    proc_b = load_processor("processors/processor_B.json")
    coupling = tuple(map(tuple, proc_b["coupling_map"]))
    n_phys = proc_b["num_qubits"]
    interaction = [(0, 2)]

    # Naive layout [0, 1, 2] requires distance 2 (2 hops = 2 SWAPs per Trotter step)
    naive_eval = evaluate_layout(coupling, n_phys, interaction, (0, 1, 2))
    assert naive_eval.swap_count > 0
    assert not naive_eval.is_direct

    # Optimal layout search finds adjacent physical pairs for (0, 2)
    optimal_candidates = find_optimal_layout(coupling, n_phys, 3, interaction)
    best = optimal_candidates[0]
    assert best.swap_count == 0
    assert best.total_dilation == 1
    assert best.is_direct


def test_symmetric_trotter_formula_structure():
    """Verify 2nd-order Trotter-Suzuki S2 preserves gate arity and bounds."""
    steps = 4
    total_time = 0.8
    gates = symmetric_trotter_circuit(steps, total_time, 1.0, 0.7, n_qubits=3, interaction=(0, 2), field_qubit=0)
    
    # Check that only rzz and rx gates are present
    assert all(g.name in {"rzz", "rx"} for g in gates)
    # Total rzz gates should equal step count
    rzz_count = sum(1 for g in gates if g.name == "rzz")
    assert rzz_count == steps


def test_unitary_folding_and_richardson_extrapolation():
    """Verify unitary gate folding scale factor and polynomial extrapolation."""
    from src.practice_s3 import Gate
    circuit = [
        Gate("rx", (0,), theta=0.5),
        Gate("cx", (0, 1)),
        Gate("rx", (1,), theta=0.5),
    ]

    folded_1 = apply_unitary_folding(circuit, 1)
    assert len(folded_1) == 3

    folded_3 = apply_unitary_folding(circuit, 3)
    # Original cx + 2 folded cx = 3 cx gates total
    assert sum(1 for g in folded_3 if g.name == "cx") == 3

    folded_5 = apply_unitary_folding(circuit, 5)
    # Original cx + 4 folded cx = 5 cx gates total
    assert sum(1 for g in folded_5 if g.name == "cx") == 5

    # Test extrapolation to lambda = 0
    # Linear trend: E(lambda) = 1.0 - 0.1 * lambda -> at lambda=0, should be 1.0
    scales = [1.0, 3.0, 5.0]
    values = [0.9, 0.7, 0.5]
    extrapolated = richardson_extrapolate(scales, values)
    assert np.isclose(extrapolated, 1.0)


def test_readout_error_inversion():
    """Verify tensored readout inversion recovers unbiased expectation."""
    # If true <Z> = 0.8, with readout_error = 0.05, measured <Z> = 0.8 * (1 - 2*0.05) = 0.72
    measured = 0.72
    recovered = invert_readout_error(measured, 0.05)
    assert np.isclose(recovered, 0.8)


def test_processor_d_graph_metrics_and_bell():
    """Verify Processor D topology has lower diameter and high Bell verification."""
    proc_d = load_processor("processors/processor_D.json")
    coupling = tuple(map(tuple, proc_d["coupling_map"]))
    metrics = compute_graph_metrics("processor_D", coupling, proc_d["num_qubits"])

    assert metrics.num_qubits == 9
    assert metrics.diameter <= 4
    assert metrics.avg_path_length < 2.5
    assert metrics.max_degree <= 4
    assert metrics.algebraic_connectivity > 0.0

    bell_result = benchmark_bell_port_correlation(proc_d)
    assert bell_result["bell_fidelity"] > 0.85
    assert bell_result["verification_metric"] > 2.0
