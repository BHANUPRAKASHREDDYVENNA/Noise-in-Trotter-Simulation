"""Processor D Design and Offline Bell-Correlation Analysis Suite.

In the Qiskit Fall Fest 2026 challenge contract:
"After shortlisting, Processor C is introduced and teams design Processor D.
The Bell-correlation challenge is completed offline using C and D."

This module implements:
1. Graph-theoretic architecture analysis (Diameter, Average Path Length, Algebraic Connectivity, Max Degree).
2. Bell-state creation, routing between designated ports, and XX/YY/ZZ correlation evaluation.
3. Comparative benchmarking across Processor A, Processor B, and custom Processor D.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import numpy as np
import pandas as pd

from src.bell_benchmark import (
    bell_correlations,
    bell_state,
    depolarizing_mix,
    fidelity_to_bell,
)
from src.processors import interaction_swap_count, undirected_adjacency
from src.validation import ValidationError


@dataclass(frozen=True)
class GraphMetrics:
    name: str
    num_qubits: int
    num_edges: int
    diameter: int
    avg_path_length: float
    max_degree: int
    algebraic_connectivity: float


def compute_graph_metrics(name: str, coupling_map: Sequence[tuple[int, int]], num_qubits: int) -> GraphMetrics:
    """Compute rigorous topological and spectral metrics for a quantum processor coupling graph."""
    adjacency = undirected_adjacency(coupling_map, num_qubits)
    num_edges = len(coupling_map)

    # Compute all-pairs shortest paths using BFS
    dist_matrix = np.full((num_qubits, num_qubits), np.inf)
    for i in range(num_qubits):
        dist_matrix[i, i] = 0
        queue = [i]
        while queue:
            curr = queue.pop(0)
            for neighbor in adjacency[curr]:
                if dist_matrix[i, neighbor] == np.inf:
                    dist_matrix[i, neighbor] = dist_matrix[i, curr] + 1
                    queue.append(neighbor)

    diameter = int(np.max(dist_matrix))
    total_pairs = num_qubits * (num_qubits - 1)
    avg_path = float(np.sum(dist_matrix[dist_matrix > 0]) / total_pairs) if total_pairs > 0 else 0.0
    max_deg = max(len(neighbors) for neighbors in adjacency)

    # Graph Laplacian L = D - A
    A = np.zeros((num_qubits, num_qubits))
    D = np.zeros((num_qubits, num_qubits))
    for i in range(num_qubits):
        D[i, i] = len(adjacency[i])
        for j in adjacency[i]:
            A[i, j] = 1.0
    L = D - A
    eigenvalues = np.sort(np.linalg.eigvalsh(L))
    # Algebraic connectivity is lambda_2
    alg_conn = float(eigenvalues[1]) if len(eigenvalues) > 1 else 0.0

    return GraphMetrics(
        name=name,
        num_qubits=num_qubits,
        num_edges=num_edges,
        diameter=diameter,
        avg_path_length=round(avg_path, 3),
        max_degree=max_deg,
        algebraic_connectivity=round(alg_conn, 4),
    )


def benchmark_bell_port_correlation(
    processor_def: dict[str, Any],
) -> dict[str, Any]:
    """Benchmark Bell pair generation and measurement across designated ports."""
    ports = processor_def.get("ports", (0, processor_def["num_qubits"] - 1))
    coupling = tuple(map(tuple, processor_def["coupling_map"]))
    n = processor_def["num_qubits"]
    p1 = float(processor_def["noise"]["single_qubit_error"])
    p2 = float(processor_def["noise"]["two_qubit_error"])
    readout = float(processor_def["noise"]["readout_error"])

    swaps = interaction_swap_count(coupling, n, ports[0], ports[1])
    two_q_gates = 1 + swaps * 3  # 1 CX for Bell creation + 3 CX per SWAP

    # Model depolarizing noise accumulated over 2Q depth:
    # Effective fidelity scale ~ (1 - p2)^two_q_gates * (1 - p1)^depth
    accumulated_noise_p = 1.0 - ((1.0 - p2) ** two_q_gates) * ((1.0 - p1) ** (two_q_gates * 2))
    accumulated_noise_p = float(np.clip(accumulated_noise_p, 0.0, 1.0))

    pure_bell = bell_state()
    noisy_density = depolarizing_mix(pure_bell, accumulated_noise_p)
    fid = fidelity_to_bell(noisy_density)

    # Correlations on noisy density
    X = np.array([[0, 1], [1, 0]], dtype=complex)
    Y = np.array([[0, -1j], [1j, 0]], dtype=complex)
    Z = np.array([[1, 0], [0, -1]], dtype=complex)

    correlations = {
        "XX": float(np.real(np.trace(noisy_density @ np.kron(X, X)))),
        "YY": float(np.real(np.trace(noisy_density @ np.kron(Y, Y)))),
        "ZZ": float(np.real(np.trace(noisy_density @ np.kron(Z, Z)))),
    }

    # Verification metric: <XX> - <YY> + <ZZ> (equals 3.0 for ideal |Phi+>)
    verification_sum = correlations["XX"] - correlations["YY"] + correlations["ZZ"]

    return {
        "name": processor_def["name"],
        "num_qubits": n,
        "ports": list(ports),
        "port_distance": swaps + 1,
        "swaps_needed": swaps,
        "total_2q_gates": two_q_gates,
        "noise_parameter": round(accumulated_noise_p, 4),
        "bell_fidelity": round(fid, 4),
        "XX": round(correlations["XX"], 4),
        "YY": round(correlations["YY"], 4),
        "ZZ": round(correlations["ZZ"], 4),
        "verification_metric": round(verification_sum, 4),
    }


def compare_all_architectures(
    root_dir: str | Path = ".",
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Run full graph and Bell benchmark comparison across Processor A, B, and D."""
    root = Path(root_dir)
    files = {
        "A": root / "processors" / "processor_A.json",
        "B": root / "processors" / "processor_B.json",
        "D": root / "processors" / "processor_D.json",
    }

    graph_rows = []
    bell_rows = []

    for label, path in files.items():
        if not path.is_file():
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        coupling = tuple(map(tuple, data["coupling_map"]))
        gm = compute_graph_metrics(data["name"], coupling, data["num_qubits"])
        graph_rows.append({
            "processor": label,
            "name": gm.name,
            "num_qubits": gm.num_qubits,
            "num_edges": gm.num_edges,
            "diameter": gm.diameter,
            "avg_path_length": gm.avg_path_length,
            "max_degree": gm.max_degree,
            "algebraic_connectivity": gm.algebraic_connectivity,
        })
        bell_metrics = benchmark_bell_port_correlation(data)
        bell_metrics["processor"] = label
        bell_rows.append(bell_metrics)

    df_graph = pd.DataFrame(graph_rows)
    df_bell = pd.DataFrame(bell_rows)
    return df_graph, df_bell
