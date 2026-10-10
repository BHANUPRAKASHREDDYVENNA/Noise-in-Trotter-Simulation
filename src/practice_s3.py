"""Validated, resource-guarded S3 practice demonstrator."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np
from scipy import sparse
from scipy.sparse.linalg import expm_multiply

from src.processors import shortest_path
from src.validation import (
    MAX_TRAJECTORIES,
    ValidationError,
    finite_real,
    probability,
    positive_int,
    validate_processor_mapping,
    validate_qubit,
    validate_statevector_size,
    validate_trotter_parameters,
)

PAULI_X = np.array([[0, 1], [1, 0]], dtype=complex)
PAULI_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
PAULI_Z = np.array([[1, 0], [0, -1]], dtype=complex)


@dataclass(frozen=True)
class Gate:
    name: str
    qubits: tuple[int, ...]
    theta: float | None = None
    role: str = "algorithm"

    def __post_init__(self) -> None:
        arity = {"rx": 1, "rzz": 2, "cx": 2}.get(self.name)
        if arity is None:
            raise ValidationError(f"Unsupported gate: {self.name}.")
        if len(self.qubits) != arity:
            raise ValidationError(f"{self.name} requires exactly {arity} qubits.")
        if any(isinstance(q, bool) or not isinstance(q, int) or q < 0 for q in self.qubits):
            raise ValidationError("Gate qubits must be non-negative integers.")
        if len(set(self.qubits)) != len(self.qubits):
            raise ValidationError("Gate qubits must be distinct.")
        if self.name in {"rx", "rzz"}:
            if self.theta is None:
                raise ValidationError(f"{self.name} requires theta.")
            finite_real("theta", self.theta)
        if self.role not in {"algorithm", "routing"}:
            raise ValidationError("Gate role must be algorithm or routing.")


@dataclass(frozen=True)
class PracticeProcessor:
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


def _validate_state(state: np.ndarray, n: int) -> None:
    positive_int("n_qubits", n)
    validate_statevector_size(n)
    if state.ndim != 1 or state.size != (1 << n):
        raise ValidationError("Statevector shape does not match n_qubits.")
    if not np.iscomplexobj(state):
        raise ValidationError("Statevector must use a complex dtype.")


def _apply_rx(state: np.ndarray, q: int, theta: float, n: int) -> np.ndarray:
    validate_qubit("q", q, n)
    out = state.copy()
    block = 1 << (n - q - 1)
    stride = block << 1
    c = np.cos(theta / 2)
    s = -1j * np.sin(theta / 2)
    for start in range(0, state.size, stride):
        left = slice(start, start + block)
        right = slice(start + block, start + stride)
        a = state[left].copy()
        b = state[right].copy()
        out[left] = c * a + s * b
        out[right] = s * a + c * b
    return out


def _apply_rzz(state: np.ndarray, q0: int, q1: int, theta: float, n: int) -> np.ndarray:
    validate_qubit("q0", q0, n)
    validate_qubit("q1", q1, n)
    if q0 == q1:
        raise ValidationError("rzz requires distinct qubits.")
    out = state.copy()
    mask0 = 1 << (n - 1 - q0)
    mask1 = 1 << (n - 1 - q1)
    phase_same = np.exp(-0.5j * theta)
    phase_diff = np.exp(0.5j * theta)
    indices = np.arange(state.size)
    same = ((indices & mask0) != 0) == ((indices & mask1) != 0)
    out[same] *= phase_same
    out[~same] *= phase_diff
    return out


def _apply_cx(state: np.ndarray, control: int, target: int, n: int) -> np.ndarray:
    validate_qubit("control", control, n)
    validate_qubit("target", target, n)
    if control == target:
        raise ValidationError("cx requires distinct qubits.")
    out = state.copy()
    control_mask = 1 << (n - 1 - control)
    target_mask = 1 << (n - 1 - target)
    for index in range(state.size):
        if index & control_mask and not (index & target_mask):
            partner = index | target_mask
            out[index] = state[partner]
            out[partner] = state[index]
    return out


def _apply_single_pauli(state: np.ndarray, pauli: np.ndarray, q: int, n: int) -> np.ndarray:
    if np.array_equal(pauli, PAULI_X):
        return _apply_rx(state, q, np.pi, n)
    out = state.copy()
    block = 1 << (n - q - 1)
    stride = block << 1
    if np.array_equal(pauli, PAULI_Y):
        for start in range(0, state.size, stride):
            left = slice(start, start + block)
            right = slice(start + block, start + stride)
            a = state[left].copy()
            b = state[right].copy()
            out[left] = -1j * b
            out[right] = 1j * a
        return out
    mask = 1 << (n - 1 - q)
    out[(np.arange(state.size) & mask) != 0] *= -1
    return out


def apply_gate(state: np.ndarray, gate: Gate, n: int) -> np.ndarray:
    _validate_state(state, n)
    if gate.name == "rx":
        return _apply_rx(state, gate.qubits[0], float(gate.theta), n)
    if gate.name == "rzz":
        return _apply_rzz(state, gate.qubits[0], gate.qubits[1], float(gate.theta), n)
    return _apply_cx(state, gate.qubits[0], gate.qubits[1], n)


def swap_gate(q0: int, q1: int) -> tuple[Gate, Gate, Gate]:
    return (
        Gate("cx", (q0, q1), role="routing"),
        Gate("cx", (q1, q0), role="routing"),
        Gate("cx", (q0, q1), role="routing"),
    )


def compile_practice(
    gates: Iterable[Gate],
    processor: PracticeProcessor,
) -> list[Gate]:
    compiled: list[Gate] = []
    for gate in gates:
        if len(gate.qubits) == 1:
            if gate.qubits[0] >= processor.num_qubits:
                raise ValidationError("Gate targets a qubit outside processor capacity.")
            compiled.append(gate)
            continue

        q0, q1 = gate.qubits
        direct = (q0, q1) in processor.coupling_map or (q1, q0) in processor.coupling_map
        if direct:
            compiled.append(gate)
            continue

        path = shortest_path(processor.coupling_map, processor.num_qubits, q0, q1)
        forward_pairs = list(zip(path[:-2], path[1:-1]))
        for a, b in forward_pairs:
            compiled.extend(swap_gate(a, b))
        compiled.append(Gate(gate.name, (path[-2], path[-1]), theta=gate.theta, role=gate.role))
        for a, b in reversed(forward_pairs):
            compiled.extend(swap_gate(a, b))
    return compiled


def logical_trotter_circuit(
    steps: int,
    total_time: float,
    J: float,
    h: float,
    *,
    n_qubits: int = 3,
    interaction: tuple[int, int] = (0, 2),
    field_qubit: int = 0,
) -> list[Gate]:
    validate_trotter_parameters(
        n_qubits=n_qubits,
        steps=steps,
        total_time=total_time,
        coupling=J,
        field=h,
    )
    validate_qubit("interaction[0]", interaction[0], n_qubits)
    validate_qubit("interaction[1]", interaction[1], n_qubits)
    validate_qubit("field_qubit", field_qubit, n_qubits)
    if interaction[0] == interaction[1]:
        raise ValidationError("interaction qubits must be distinct.")

    dt = total_time / steps
    return [
        gate
        for _ in range(steps)
        for gate in (
            Gate("rzz", interaction, theta=2 * J * dt),
            Gate("rx", (field_qubit,), theta=2 * h * dt),
        )
    ]



def ideal_exact_state(
    n: int,
    total_time: float,
    J: float,
    h: float,
    *,
    interaction: tuple[int, int] = (0, 2),
    field_qubit: int = 0,
) -> np.ndarray:
    validate_trotter_parameters(
        n_qubits=n,
        steps=1,
        total_time=total_time,
        coupling=J,
        field=h,
    )
    validate_qubit("interaction[0]", interaction[0], n)
    validate_qubit("interaction[1]", interaction[1], n)
    validate_qubit("field_qubit", field_qubit, n)
    if interaction[0] == interaction[1]:
        raise ValidationError("interaction qubits must be distinct.")
    validate_statevector_size(n)

    identity = sparse.identity(2, dtype=complex, format="csr")
    z = sparse.csr_matrix(PAULI_Z)
    x = sparse.csr_matrix(PAULI_X)
    zz_ops = [z if qubit in set(interaction) else identity for qubit in range(n)]
    x_ops = [x if qubit == field_qubit else identity for qubit in range(n)]

    def kron_chain(ops: list[sparse.spmatrix]) -> sparse.csr_matrix:
        result = ops[0]
        for operator in ops[1:]:
            result = sparse.kron(result, operator, format="csr")
        return result

    hamiltonian = J * kron_chain(zz_ops) + h * kron_chain(x_ops)
    psi0 = np.zeros(1 << n, dtype=complex)
    psi0[0] = 1.0
    state = expm_multiply((-1j * total_time) * hamiltonian, psi0)
    norm = np.linalg.norm(state)
    if not np.isfinite(norm) or norm <= 0:
        raise RuntimeError("Exact state propagation produced an invalid statevector.")
    return state / norm


def _simulate_noisy_trajectory(
    gates: Sequence[Gate],
    processor: PracticeProcessor,
    n: int,
    rng: np.random.Generator,
) -> np.ndarray:
    state = np.zeros(1 << n, dtype=complex)
    state[0] = 1.0

    for gate in gates:
        state = apply_gate(state, gate, n)
        if len(gate.qubits) == 1 and rng.random() < processor.p1:
            pauli = (PAULI_X, PAULI_Y, PAULI_Z)[int(rng.integers(0, 3))]
            state = _apply_single_pauli(state, pauli, gate.qubits[0], n)
        elif len(gate.qubits) == 2 and rng.random() < processor.p2:
            for qubit in gate.qubits:
                pauli = (PAULI_X, PAULI_Y, PAULI_Z)[int(rng.integers(0, 3))]
                state = _apply_single_pauli(state, pauli, qubit, n)
    return state


def _z_expectation(state: np.ndarray, q: int, n: int) -> float:
    mask = 1 << (n - 1 - q)
    probabilities = np.abs(state) ** 2
    indices = np.arange(state.size)
    return float(np.sum(probabilities * np.where((indices & mask) != 0, -1.0, 1.0)))


def run_noisy_trajectory(
    gates: Sequence[Gate],
    processor: PracticeProcessor,
    exact_state: np.ndarray,
    rng: np.random.Generator,
    n: int,
) -> float:
    state = _simulate_noisy_trajectory(gates, processor, n, rng)
    overlap = np.vdot(exact_state, state)
    return float(np.clip(np.abs(overlap) ** 2, 0.0, 1.0))


def count_metrics(gates: Sequence[Gate], n: int) -> dict[str, float]:
    positive_int("n_qubits", n)
    last_layer = [0] * n
    depth = 0
    two_qubit = 0
    routing_two_qubit = 0

    for gate in gates:
        if any(q >= n for q in gate.qubits):
            raise ValidationError("Gate references a qubit outside processor capacity.")
        layer = max((last_layer[q] for q in gate.qubits), default=0) + 1
        for q in gate.qubits:
            last_layer[q] = layer
        depth = max(depth, layer)
        if len(gate.qubits) == 2:
            two_qubit += 1
            routing_two_qubit += int(gate.role == "routing")

    if routing_two_qubit % 3:
        raise ValidationError("Routing CX count must be divisible by 3.")

    return {
        "physical_qubits": float(n),
        "depth": float(depth),
        "two_qubit_gate_count": float(two_qubit),
        "swap_count": float(routing_two_qubit // 3),
        "routing_two_qubit_gate_count": float(routing_two_qubit),
        "algorithmic_two_qubit_gate_count": float(two_qubit - routing_two_qubit),
    }


def _online_update(
    count: int,
    mean: float,
    m2: float,
    value: float,
) -> tuple[int, float, float]:
    count += 1
    delta = value - mean
    mean += delta / count
    m2 += delta * (value - mean)
    return count, mean, m2


def benchmark_processor(
    processor: PracticeProcessor,
    logical_gates: Sequence[Gate],
    exact_state: np.ndarray,
    n: int,
    trajectories: int,
    seed: int,
) -> dict[str, float]:
    positive_int("trajectories", trajectories, maximum=MAX_TRAJECTORIES)
    _validate_state(exact_state, n)

    compiled = compile_practice(logical_gates, processor)
    rng = np.random.default_rng(seed)
    count = 0
    fidelity_mean = fidelity_m2 = 0.0
    z_mean = z_m2 = 0.0
    measured_z_mean = measured_z_m2 = 0.0

    for _ in range(trajectories):
        state = _simulate_noisy_trajectory(compiled, processor, n, rng)
        fidelity = float(np.clip(np.abs(np.vdot(exact_state, state)) ** 2, 0.0, 1.0))
        z0 = _z_expectation(state, 0, n)
        measured_z0 = (1.0 - 2.0 * processor.readout_error) * z0

        count, fidelity_mean, fidelity_m2 = _online_update(
            count, fidelity_mean, fidelity_m2, fidelity
        )
        _, z_mean, z_m2 = _online_update(count - 1, z_mean, z_m2, z0)
        _, measured_z_mean, measured_z_m2 = _online_update(
            count - 1, measured_z_mean, measured_z_m2, measured_z0
        )

    divisor = max(count - 1, 1)
    fidelity_std = float(np.sqrt(max(fidelity_m2 / divisor, 0.0))) if count > 1 else 0.0
    z_std = float(np.sqrt(max(z_m2 / divisor, 0.0))) if count > 1 else 0.0
    measured_z_std = (
        float(np.sqrt(max(measured_z_m2 / divisor, 0.0))) if count > 1 else 0.0
    )

    metrics = count_metrics(compiled, n)
    metrics.update(
        {
            "mean_fidelity": fidelity_mean,
            "fidelity_std": fidelity_std,
            "fidelity_stderr": fidelity_std / np.sqrt(count),
            "mean_z0_expectation": z_mean,
            "z0_expectation_std": z_std,
            "measured_z0_expectation": measured_z_mean,
            "measured_z0_expectation_std": measured_z_std,
            "trajectories": float(count),
        }
    )
    return metrics
