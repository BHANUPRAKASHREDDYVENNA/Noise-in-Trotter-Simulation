"""Self-contained S3-style demonstrator derived from the supplied QFF Phase-1 guide.

The numerical Hamiltonian, noise rates and processor settings in this module are
explicitly illustrative and kept separate from any organizer-defined result.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

import numpy as np
from scipy.linalg import expm


PAULI_I = np.eye(2, dtype=complex)
PAULI_X = np.array([[0, 1], [1, 0]], dtype=complex)
PAULI_Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
PAULI_Z = np.array([[1, 0], [0, -1]], dtype=complex)


@dataclass(frozen=True)
class Gate:
    name: str
    qubits: tuple[int, ...]
    theta: float | None = None


@dataclass(frozen=True)
class PracticeProcessor:
    name: str
    num_qubits: int
    coupling_map: tuple[tuple[int, int], ...]
    p1: float
    p2: float
    readout_error: float


def kron_n(ops: Sequence[np.ndarray]) -> np.ndarray:
    out = np.array([[1.0 + 0j]])
    for op in ops:
        out = np.kron(out, op)
    return out


def embed_single(op: np.ndarray, q: int, n: int) -> np.ndarray:
    ops = [PAULI_I] * n
    ops[q] = op
    return kron_n(ops)


def embed_two(op: np.ndarray, q0: int, q1: int, n: int) -> np.ndarray:
    """Embed a 4x4 operator on q0/q1 using the project's fixed qubit ordering."""
    if q0 == q1:
        raise ValueError("Two-qubit gate needs distinct qubits")
    dim = 2**n
    full = np.zeros((dim, dim), dtype=complex)
    mask0 = 1 << (n - 1 - q0)
    mask1 = 1 << (n - 1 - q1)
    for col in range(dim):
        b0 = 1 if col & mask0 else 0
        b1 = 1 if col & mask1 else 0
        local_col = (b0 << 1) | b1
        for local_row in range(4):
            r0 = (local_row >> 1) & 1
            r1 = local_row & 1
            row = col
            if r0 != b0:
                row ^= mask0
            if r1 != b1:
                row ^= mask1
            full[row, col] += op[local_row, local_col]
    return full


def rx(theta: float) -> np.ndarray:
    return np.cos(theta / 2) * PAULI_I - 1j * np.sin(theta / 2) * PAULI_X


def rzz(theta: float) -> np.ndarray:
    zz = np.kron(PAULI_Z, PAULI_Z)
    return expm(-1j * theta / 2 * zz)


def cx() -> np.ndarray:
    return np.array(
        [[1, 0, 0, 0],
         [0, 1, 0, 0],
         [0, 0, 0, 1],
         [0, 0, 1, 0]],
        dtype=complex,
    )


def swap_gate() -> tuple[Gate, Gate, Gate]:
    return Gate("cx", (0, 1)), Gate("cx", (1, 0)), Gate("cx", (0, 1))


def logical_trotter_circuit(steps: int, total_time: float, J: float, h: float) -> list[Gate]:
    dt = total_time / steps
    gates: list[Gate] = []
    for _ in range(steps):
        gates.append(Gate("rzz", (0, 2), theta=2 * J * dt))
        gates.append(Gate("rx", (0,), theta=2 * h * dt))
    return gates


def compile_practice(gates: Iterable[Gate], processor: PracticeProcessor) -> list[Gate]:
    """Compile the logical 0-2 interaction for either illustrative topology."""
    compiled: list[Gate] = []
    for gate in gates:
        if gate.name == "rzz" and tuple(sorted(gate.qubits)) == (0, 2):
            if (0, 2) in processor.coupling_map or (2, 0) in processor.coupling_map:
                compiled.append(gate)
            else:
                compiled.extend([Gate("cx", (0, 1)), Gate("cx", (1, 0)), Gate("cx", (0, 1))])
                compiled.append(Gate("rzz", (1, 2), theta=gate.theta))
                compiled.extend([Gate("cx", (0, 1)), Gate("cx", (1, 0)), Gate("cx", (0, 1))])
        else:
            compiled.append(gate)
    return compiled


def ideal_exact_state(n: int, total_time: float, J: float, h: float) -> np.ndarray:
    zz = embed_two(np.kron(PAULI_Z, PAULI_Z), 0, 2, n)
    x0 = embed_single(PAULI_X, 0, n)
    H = J * zz + h * x0
    psi0 = np.zeros(2**n, dtype=complex)
    psi0[0] = 1.0
    return expm(-1j * H * total_time) @ psi0


def apply_gate(state: np.ndarray, gate: Gate, n: int) -> np.ndarray:
    if gate.name == "rx":
        U = embed_single(rx(float(gate.theta)), gate.qubits[0], n)
    elif gate.name == "rzz":
        U = embed_two(rzz(float(gate.theta)), gate.qubits[0], gate.qubits[1], n)
    elif gate.name == "cx":
        U = embed_two(cx(), gate.qubits[0], gate.qubits[1], n)
    else:
        raise ValueError(f"Unsupported practice gate: {gate.name}")
    return U @ state


def random_pauli_1(rng: np.random.Generator) -> np.ndarray:
    return [PAULI_X, PAULI_Y, PAULI_Z][int(rng.integers(0, 3))]


def random_pauli_2(rng: np.random.Generator) -> np.ndarray:
    choices = [PAULI_X, PAULI_Y, PAULI_Z]
    a = choices[int(rng.integers(0, 3))]
    b = choices[int(rng.integers(0, 3))]
    return np.kron(a, b)


def run_noisy_trajectory(
    gates: Sequence[Gate],
    processor: PracticeProcessor,
    exact_state: np.ndarray,
    rng: np.random.Generator,
    n: int,
) -> float:
    state = np.zeros(2**n, dtype=complex)
    state[0] = 1.0
    for gate in gates:
        state = apply_gate(state, gate, n)
        if len(gate.qubits) == 1 and rng.random() < processor.p1:
            state = embed_single(random_pauli_1(rng), gate.qubits[0], n) @ state
        elif len(gate.qubits) == 2 and rng.random() < processor.p2:
            state = embed_two(random_pauli_2(rng), gate.qubits[0], gate.qubits[1], n) @ state
    overlap = np.vdot(exact_state, state)
    return float(np.abs(overlap) ** 2)


def count_metrics(gates: Sequence[Gate], n: int) -> dict[str, float]:
    two_q = sum(1 for g in gates if len(g.qubits) == 2)
    routing_cx = sum(1 for g in gates if g.name == "cx")
    rzz_count = sum(1 for g in gates if g.name == "rzz")
    rx_count = sum(1 for g in gates if g.name == "rx")
    swaps = routing_cx // 3
    last_layer = [0] * n
    depth = 0
    for gate in gates:
        qubit_layers = [last_layer[q] for q in gate.qubits]
        layer = (max(qubit_layers) if qubit_layers else 0) + 1
        for q in gate.qubits:
            last_layer[q] = layer
        depth = max(depth, layer)
    return {
        "physical_qubits": float(n),
        "depth": float(depth),
        "two_qubit_gate_count": float(two_q),
        "swap_count": float(swaps),
        "rzz_count": float(rzz_count),
        "rx_count": float(rx_count),
        "cx_count": float(routing_cx),
    }


def benchmark_processor(
    processor: PracticeProcessor,
    logical_gates: Sequence[Gate],
    exact_state: np.ndarray,
    n: int,
    trajectories: int,
    seed: int,
) -> dict[str, float]:
    compiled = compile_practice(logical_gates, processor)
    rng = np.random.default_rng(seed)
    fidelities = [
        run_noisy_trajectory(compiled, processor, exact_state, rng, n)
        for _ in range(trajectories)
    ]
    m = count_metrics(compiled, n)
    m.update(
        {
            "mean_fidelity": float(np.mean(fidelities)),
            "fidelity_std": float(np.std(fidelities, ddof=1)) if trajectories > 1 else 0.0,
            "trajectories": float(trajectories),
        }
    )
    return m
