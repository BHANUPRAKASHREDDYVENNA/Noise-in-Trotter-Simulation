from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from src.processors import interaction_swap_count
from src.validation import ValidationError, probability, positive_int, validate_processor_mapping

I = np.eye(2, dtype=complex)
X = np.array([[0, 1], [1, 0]], dtype=complex)
Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
Z = np.array([[1, 0], [0, -1]], dtype=complex)


@dataclass(frozen=True)
class ProcessorModel:
    name: str
    num_qubits: int
    coupling_map: tuple[tuple[int, int], ...]
    p1: float
    p2: float
    readout_error: float

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValidationError("Processor name must be non-empty.")
        positive_int("num_qubits", self.num_qubits)
        validate_processor_mapping(self.coupling_map, self.num_qubits)
        probability("p1", self.p1)
        probability("p2", self.p2)
        probability("readout_error", self.readout_error)


def kron_all(ops: Iterable[np.ndarray]) -> np.ndarray:
    ops = tuple(ops)
    if not ops:
        raise ValidationError("At least one operator is required.")
    result = np.array([[1.0 + 0.0j]])
    for op in ops:
        result = np.kron(result, op)
    return result


def bell_state() -> np.ndarray:
    state = np.zeros(4, dtype=complex)
    state[0] = 1 / np.sqrt(2)
    state[3] = 1 / np.sqrt(2)
    return state


def bell_density() -> np.ndarray:
    psi = bell_state()
    return np.outer(psi, psi.conj())


def expectation(state: np.ndarray, observable: np.ndarray) -> float:
    if state.ndim != 1:
        raise ValidationError("state must be a vector.")
    return float(np.real(np.vdot(state, observable @ state)))


def bell_correlations(state: np.ndarray) -> dict[str, float]:
    return {
        "XX": expectation(state, np.kron(X, X)),
        "YY": expectation(state, np.kron(Y, Y)),
        "ZZ": expectation(state, np.kron(Z, Z)),
    }


def depolarizing_mix(state: np.ndarray, p: float) -> np.ndarray:
    p = probability("p", p)
    rho = np.outer(state, state.conj())
    dimension = rho.shape[0]
    return (1.0 - p) * rho + p * np.eye(dimension, dtype=complex) / dimension


def density_expectation(rho: np.ndarray, observable: np.ndarray) -> float:
    if rho.ndim != 2:
        raise ValidationError("rho must be a matrix.")
    return float(np.real(np.trace(rho @ observable)))


def fidelity_to_bell(rho: np.ndarray) -> float:
    psi = bell_state()
    return float(np.clip(np.real(np.vdot(psi, rho @ psi)), 0.0, 1.0))


def postselect_bell_z_counts(counts: dict[str, int]) -> tuple[int, int]:
    if not counts:
        raise ValidationError("counts must not be empty.")
    accepted = int(counts.get("00", 0) + counts.get("11", 0))
    total = int(sum(counts.values()))
    if total <= 0 or accepted > total:
        raise ValidationError("Invalid measurement counts.")
    return accepted, total


def bell_measurement_probs(rho: np.ndarray) -> dict[str, float]:
    probs = np.real(np.diag(rho))
    if len(probs) != 4:
        raise ValidationError("Bell measurement requires a two-qubit state.")
    clipped = np.clip(probs, 0.0, None)
    total = float(clipped.sum())
    if total <= 0 or not np.isfinite(total):
        raise ValidationError("Bell measurement probabilities are invalid.")
    clipped /= total
    return {format(i, "02b"): float(clipped[i]) for i in range(4)}


def apply_readout_error(probs: dict[str, float], readout_error: float) -> dict[str, float]:
    readout_error = probability("readout_error", readout_error)
    if set(probs) != {"00", "01", "10", "11"}:
        raise ValidationError("Bell readout probabilities must contain all four basis states.")

    out = {label: 0.0 for label in probs}
    for source, source_prob in probs.items():
        if not np.isfinite(source_prob) or source_prob < 0:
            raise ValidationError("Readout input probabilities must be finite and non-negative.")
        bits = [int(source[0]), int(source[1])]
        for flip0 in (0, 1):
            for flip1 in (0, 1):
                mass = source_prob * (readout_error if flip0 else 1.0 - readout_error) * (readout_error if flip1 else 1.0 - readout_error)
                measured = f"{bits[0] ^ flip0}{bits[1] ^ flip1}"
                out[measured] += mass

    if not np.isclose(sum(out.values()), 1.0, atol=1e-12):
        raise ValidationError("Readout probabilities do not sum to one.")
    return out


def sample_counts(probs: dict[str, float], shots: int, rng: np.random.Generator) -> dict[str, int]:
    positive_int("shots", shots, maximum=10_000_000)
    labels = list(probs)
    values = np.array([probs[label] for label in labels], dtype=float)
    if not labels or not np.all(np.isfinite(values)) or np.any(values < 0):
        raise ValidationError("Invalid measurement probabilities.")
    if not np.isclose(float(values.sum()), 1.0, atol=1e-12):
        raise ValidationError("Measurement probabilities must sum to one.")
    sampled = rng.multinomial(shots, values)
    return {label: int(n) for label, n in zip(labels, sampled)}


def proportion_standard_error(p: float, n: int) -> float:
    positive_int("n", n)
    p = probability("p", p)
    return float(np.sqrt(p * (1.0 - p) / n))


def benchmark_bell_processor(
    processor: ProcessorModel,
    shots: int = 2048,
    seed: int = 7,
    logical_depth: int = 2,
    routing_swaps: int | None = None,
) -> dict[str, float]:
    positive_int("shots", shots, maximum=10_000_000)
    positive_int("logical_depth", logical_depth, maximum=1_000_000)

    if routing_swaps is None:
        ports = (0, 1) if processor.num_qubits < 5 else (0, 4)
        routing_swaps = interaction_swap_count(
            processor.coupling_map,
            processor.num_qubits,
            ports[0],
            ports[1],
            restore_layout=False,
        )
    if isinstance(routing_swaps, bool) or not isinstance(routing_swaps, int) or routing_swaps < 0:
        raise ValidationError("routing_swaps must be a non-negative integer.")

    effective_2q = 1 + 3 * routing_swaps
    single_qubit_events = max(logical_depth - 1, 0)
    no_error_probability = (1.0 - processor.p2) ** effective_2q * (1.0 - processor.p1) ** single_qubit_events
    effective_noise = float(np.clip(1.0 - no_error_probability, 0.0, 0.99))

    rho = depolarizing_mix(bell_state(), effective_noise)
    xx = density_expectation(rho, np.kron(X, X))
    yy = density_expectation(rho, np.kron(Y, Y))
    zz = density_expectation(rho, np.kron(Z, Z))
    fidelity = fidelity_to_bell(rho)

    measured_probs = apply_readout_error(bell_measurement_probs(rho), processor.readout_error)
    counts = sample_counts(measured_probs, shots, np.random.default_rng(seed))
    accepted, total = postselect_bell_z_counts(counts)
    yield_rate = accepted / total

    return {
        "processor": processor.name,
        "fidelity": fidelity,
        "fidelity_uncertainty_proxy": float(np.sqrt(max(fidelity * (1.0 - fidelity), 0.0) / shots)),
        "XX": xx,
        "YY": yy,
        "ZZ": zz,
        "depth": float(logical_depth + 3 * routing_swaps),
        "two_qubit_gates": float(effective_2q),
        "swap_overhead": float(routing_swaps),
        "physical_qubits": float(processor.num_qubits),
        "postselection_yield": float(yield_rate),
        "postselection_yield_se": float(proportion_standard_error(yield_rate, total)),
        "shots": float(shots),
        "effective_noise": effective_noise,
        "readout_error": processor.readout_error,
    }
