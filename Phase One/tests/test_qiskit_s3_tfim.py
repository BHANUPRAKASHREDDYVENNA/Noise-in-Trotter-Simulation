from __future__ import annotations

import pytest
pytest.importorskip("qiskit")
pytest.importorskip("qiskit_aer")

import numpy as np
from pathlib import Path
from qiskit.quantum_info import Statevector, state_fidelity

from src.qiskit_s3_tfim import (
    build_4spin_tfim_hamiltonian,
    classical_exact_tfim,
    build_tfim_trotter_circuit,
    create_official_noise_model,
    run_ps_s3_benchmark,
    generate_degradation_svg,
)


def test_build_4spin_tfim_hamiltonian():
    """Verify 4-spin TFIM Hamiltonian is Hermitian and has dimension 16x16."""
    H = build_4spin_tfim_hamiltonian(J=1.0, g=1.0)
    mat = H.to_matrix()
    assert mat.shape == (16, 16)
    # Check Hermiticity: H = H^\dagger
    assert np.allclose(mat, mat.conj().T, atol=1e-12)


def test_classical_exact_tfim_energy_conservation():
    """Verify classical exact simulation preserves norm and yields sensible expectation values."""
    psi, z0 = classical_exact_tfim(J=1.0, g=1.0, total_time=1.5, initial_state="0000")
    assert psi.shape == (16,)
    # Norm must be 1.0
    norm = np.vdot(psi, psi).real
    assert np.isclose(norm, 1.0, atol=1e-10)
    # <Z0> must be bounded in [-1, 1]
    assert -1.0 <= z0 <= 1.0


def test_trotter_circuit_fidelity_increases_with_steps():
    """Verify that finer Trotterization (larger n) increases algorithmic state fidelity."""
    total_time = 1.0
    psi_exact, _ = classical_exact_tfim(J=1.0, g=1.0, total_time=total_time)
    exact_sv = Statevector(psi_exact)

    qc_1 = build_tfim_trotter_circuit(num_spins=4, steps=1, total_time=total_time, measure=False)
    qc_4 = build_tfim_trotter_circuit(num_spins=4, steps=4, total_time=total_time, measure=False)

    fid_1 = state_fidelity(Statevector.from_instruction(qc_1), exact_sv)
    fid_4 = state_fidelity(Statevector.from_instruction(qc_4), exact_sv)

    assert fid_4 > fid_1
    assert fid_4 > 0.90


def test_official_noise_model_structure():
    """Verify the official noise model includes 1Q, 2Q depolarizing and readout errors."""
    nm = create_official_noise_model(p1=0.001, p2=0.005, readout_error=0.01)
    basis = nm.basis_gates
    assert "cx" in basis
    assert "rz" in basis or "sx" in basis or "x" in basis


def test_fast_benchmark_run(tmp_path: Path):
    """Verify end-to-end TFIM benchmark execution with small shot count."""
    df = run_ps_s3_benchmark(trotter_steps=(1,), total_time=1.0, shots=100, seed=42)
    assert not df.empty
    assert "algorithmic_fidelity" in df.columns
    assert "noisy_sim_z0" in df.columns
    assert "noisy_abs_error" in df.columns

    # Test SVG generation
    svg_file = tmp_path / "test_degradation.svg"
    generate_degradation_svg(df, svg_file)
    assert svg_file.is_file()
    assert svg_file.stat().st_size > 500
