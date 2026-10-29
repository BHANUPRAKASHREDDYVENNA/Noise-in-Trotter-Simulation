from __future__ import annotations

import json
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]

import qff_sim


def test_phase2_processor_d_schema_and_validation():
    """Verify Processor D satisfies all official Phase 2 design rules."""
    proc_d_path = ROOT / "processors" / "processor_D.json"
    assert proc_d_path.is_file(), "processor_D.json must exist"

    proc_d = qff_sim.load_processor(str(proc_d_path))
    errs = qff_sim.validate_processor_d(proc_d, required_qubits=4)
    assert not errs, f"Processor D failed validation rules: {errs}"

    # Verify key architectural properties
    assert proc_d["num_qubits"] <= 12
    assert len(proc_d["justification"].split()) >= 40
    assert proc_d["basis_gates"] == ["rz", "sx", "x", "cx"]
    assert proc_d["error_rates"]["p1"] >= 0.001
    assert proc_d["error_rates"]["p2"] >= 0.005
    assert proc_d["error_rates"]["p_readout"] >= 0.01


def test_tfim_ring_hamiltonian_and_spectrum():
    """Verify 4-spin ring TFIM Hamiltonian is Hermitian and has expected spectrum."""
    H = qff_sim.tfim_hamiltonian(4, J=1.0, g=1.0, periodic=True)
    mat = H.to_matrix()
    assert mat.shape == (16, 16)
    assert np.allclose(mat, mat.conj().T, atol=1e-12), "Hamiltonian must be Hermitian"

    w, v = qff_sim.exact_spectrum(H, k=2)
    assert len(w) == 2
    assert w[0] <= w[1]


def test_trotter_circuit_properties():
    """Verify 1st order Trotter circuit on ring TFIM has expected gate counts."""
    c = qff_sim.trotter_circuit(4, J=1.0, g=1.0, t=2.0, steps=4, order=1, zz_mode="cx", periodic=True)
    assert c.num_qubits == 4
    # 4 steps x 4 bonds = 16 ZZ terms. In CX mode, each ZZ has 2 CX -> 32 logical CX gates
    metrics = qff_sim.circuit_metrics(c, qff_sim.PROCESSOR_B)
    assert metrics["logical_cx"] == 32
    assert metrics["executable"] is True


def test_bell_state_ideal_exactness():
    """Verify Bell state preparation on directly connected pair yields ideal correlation."""
    proc_d = qff_sim.load_processor(str(ROOT / "processors" / "processor_D.json"))
    res = qff_sim.bell_experiment(proc_d, (0, 1), noisy=False, shots=1024)
    assert res["fidelity"] == 1.0
    assert res["XX"] == 1.0
    assert res["YY"] == -1.0
    assert res["ZZ"] == 1.0


def test_phase2_csv_tables_exist_and_match_schema():
    """Verify all 5 required Phase 2 CSV files exist with exact columns from results_columns.md."""
    tables_dir = ROOT / "results" / "tables"

    # 1. bell.csv
    df_bell = pd.read_csv(tables_dir / "bell.csv")
    expected_bell_cols = [
        "pair", "pair_distance", "condition", "two_qubit_gates",
        "XX", "XX_se", "YY", "YY_se", "ZZ", "ZZ_se", "fidelity", "fidelity_se"
    ]
    assert list(df_bell.columns) == expected_bell_cols
    assert len(df_bell) == 4

    # 2. resources.csv
    df_res = pd.read_csv(tables_dir / "resources.csv")
    expected_res_cols = [
        "ps", "circuit_label", "processor", "executable", "logical_qubits",
        "physical_qubits", "logical_2q", "two_q", "depth", "two_q_depth",
        "swaps", "routing_overhead_2q"
    ]
    assert list(df_res.columns) == expected_res_cols
    assert len(df_res) >= 15

    # 3. s3_scan.csv
    df_scan = pd.read_csv(tables_dir / "s3_scan.csv")
    expected_scan_cols = [
        "processor", "noise_scale", "steps", "fidelity_noisy",
        "fidelity_trotter_ideal", "ms_noisy", "ms_noisy_se", "ms_exact",
        "logical_2q", "swap_2q", "two_q"
    ]
    assert list(df_scan.columns) == expected_scan_cols
    assert len(df_scan) == 60  # 5 series x 12 step counts

    # 4. s3_summary.csv
    df_sum = pd.read_csv(tables_dir / "s3_summary.csv")
    expected_sum_cols = ["processor", "noise_scale", "n_star", "fidelity_at_n_star"]
    assert list(df_sum.columns) == expected_sum_cols
    assert len(df_sum) == 5

    # 5. mitigation.csv
    df_mit = pd.read_csv(tables_dir / "mitigation.csv")
    expected_mit_cols = ["method", "ms_raw", "ms_mitigated", "extra_shots"]
    assert list(df_mit.columns) == expected_mit_cols
    assert len(df_mit) >= 1


def test_phase2_figures_exist():
    """Verify all 6 publication figures exist and are non-empty."""
    figs_dir = ROOT / "results" / "figures"
    expected_figs = [
        "s3_fidelity_crossover.png",
        "s3_noise_sweep_D.png",
        "s3_gate_split.png",
        "bell_correlations_D.png",
        "s3_zne_mitigation.png",
        "processor_topologies.png",
    ]
    for fig_name in expected_figs:
        fig_path = figs_dir / fig_name
        assert fig_path.is_file(), f"Missing figure: {fig_name}"
        assert fig_path.stat().st_size > 1000, f"Figure {fig_name} is too small or corrupted"
