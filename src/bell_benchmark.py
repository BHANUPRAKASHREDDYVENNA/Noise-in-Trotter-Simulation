"""Bell-correlation architecture benchmark derived from the supplied QFF guide."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np


I = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)
H = (1 / np.sqrt(2)) * np.array([[1, 1], [1, -1]], dtype=complex)


@dataclass(frozen=True)
class ProcessorModel:
    name: str
    num_qubits: int
    coupling_map: tuple[tuple[int, int], ...]
    p1: float
    p2: float
    readout_error: float


def kron_all(ops: Iterable[np.ndarray]) -> np.ndarray:
    result = np.array([[1.0 + 0.0j]])
    for op in ops:
        result = np.kron(result, op)
    return result


def embed_single(op: np.ndarray, q: int, n: int) -> np.ndarray:
    ops = [I] * n
    ops[q] = op
    return kron_all(ops)


def embed_two(op: np.ndarray, q0: int, q1: int, n: int) -> np.ndarray:
    if q0 == q1:
        raise ValueError("Two-qubit operator requires distinct qubits")
    dim = 2**n
    full = np.zeros((dim, dim), dtype=complex)
    m0 = 1 << (n - 1 - q0)
    m1 = 1 << (n - 1 - q1)
    for col in range(dim):
        b0 = 1 if col & m0 else 0
        b1 = 1 if col & m1 else 0
        local_col = 2 * b0 + b1
        for local_row in range(4):
            r0 = local_row // 2
            r1 = local_row % 2
            row = col
            if r0 != b0:
                row ^= m0
            if r1 != b1:
                row ^= m1
            full[row, col] += op[local_row, local_col]
    return full


def bell_state() -> np.ndarray:
    """Prepare |Phi+> = (|00> + |11>)/sqrt(2)."""
    state = np.zeros(4, dtype=complex)
    state[0] = 1 / np.sqrt(2)
    state[3] = 1 / np.sqrt(2)
    return state


def bell_density() -> np.ndarray:
    psi = bell_state()
    return np.outer(psi, psi.conj())


def expectation(state: np.ndarray, observable: np.ndarray) -> float:
    return float(np.real(np.vdot(state, observable @ state)))


def bell_correlations(state: np.ndarray) -> dict[str, float]:
    return {
        "XX": expectation(state, np.kron(X, X)),
        "YY": expectation(state, np.kron(Y, Y)),
        "ZZ": expectation(state, np.kron(Z, Z)),
    }


def depolarizing_mix(state: np.ndarray, p: float) -> np.ndarray:
    """Simple density-matrix depolarization used by the self-contained benchmark."""
    rho = np.outer(state, state.conj())
    d = rho.shape[0]
    return (1 - p) * rho + p * np.eye(d) / d


def density_expectation(rho: np.ndarray, observable: np.ndarray) -> float:
    return float(np.real(np.trace(rho @ observable)))


def fidelity_to_bell(rho: np.ndarray) -> float:
    psi = bell_state()
    return float(np.real(np.vdot(psi, rho @ psi)))


def z_parity_probability(rho: np.ndarray) -> float:
    """Probability of observing 00 or 11 in the computational basis."""
    probs = np.real(np.diag(rho))
    return float(probs[0] + probs[3])


def postselect_bell_z_counts(counts: dict[str, int]) -> tuple[int, int]:
    accepted = int(counts.get("00", 0) + counts.get("11", 0))
    total = int(sum(counts.values()))
    return accepted, total


def bell_measurement_probs(rho: np.ndarray) -> dict[str, float]:
    probs = np.clip(np.real(np.diag(rho)), 0, 1)
    return {format(i, "02b"): float(probs[i]) for i in range(4)}


def sample_counts(probs: dict[str, float], shots: int, rng: np.random.Generator) -> dict[str, int]:
    labels = list(probs)
    p = np.array([probs[k] for k in labels], dtype=float)
    p /= p.sum()
    sampled = rng.multinomial(shots, p)
    return {label: int(n) for label, n in zip(labels, sampled)}


def proportion_standard_error(p: float, n: int) -> float:
    if n <= 0:
        raise ValueError("n must be positive")
    return float(np.sqrt(p * (1 - p) / n))


def benchmark_bell_processor(
    processor: ProcessorModel,
    shots: int = 2048,
    seed: int = 7,
    logical_depth: int = 2,
    routing_swaps: int = 0,
) -> dict[str, float]:
    """Run a compact analytical Bell benchmark with architecture-aware noise."""
    rng = np.random.default_rng(seed)

    effective_2q = 1 + 3 * routing_swaps
    effective_noise = min(0.99, processor.p2 * effective_2q + processor.p1 * max(logical_depth - 1, 0))

    rho = depolarizing_mix(bell_state(), effective_noise)
    zz = density_expectation(rho, np.kron(Z, Z))
    xx = density_expectation(rho, np.kron(X, X))
    yy = density_expectation(rho, np.kron(Y, Y))
    fidelity = fidelity_to_bell(rho)

    probs = bell_measurement_probs(rho)
    counts = sample_counts(probs, shots, rng)
    accepted, total = postselect_bell_z_counts(counts)
    yield_rate = accepted / total
    yield_se = proportion_standard_error(yield_rate, total)

    return {
        "processor": processor.name,
        "fidelity": fidelity,
        "fidelity_uncertainty_proxy": float(np.sqrt(max(fidelity * (1 - fidelity), 0) / shots)),
        "XX": xx,
        "YY": yy,
        "ZZ": zz,
        "depth": float(logical_depth + 3 * routing_swaps),
        "two_qubit_gates": float(effective_2q),
        "swap_overhead": float(routing_swaps),
        "physical_qubits": float(processor.num_qubits),
        "postselection_yield": float(yield_rate),
        "postselection_yield_se": float(yield_se),
        "shots": float(shots),
    }
