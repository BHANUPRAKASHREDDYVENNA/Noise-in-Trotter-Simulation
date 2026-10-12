"""Source-document-defined online A/B benchmark for S3."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Sequence

import numpy as np
import pandas as pd

from src.practice_s3 import (
    Gate,
    PracticeProcessor,
    _online_update,
    _simulate_noisy_trajectory,
    _z_expectation,
    count_metrics,
    ideal_exact_state,
    logical_trotter_circuit,
)
from src.processors import load_processor, shortest_path
from src.validation import (
    MAX_TRAJECTORIES,
    ValidationError,
    nonnegative_int,
    positive_int,
    validate_qubit,
    validate_statevector_size,
)


ROOT = Path(__file__).resolve().parents[1]


def validate_layout(
    layout: Sequence[int],
    logical_qubits: int,
    physical_qubits: int,
) -> tuple[int, ...]:
    positive_int("logical_qubits", logical_qubits)
    positive_int("physical_qubits", physical_qubits)
    if logical_qubits > physical_qubits:
        raise ValidationError("logical_qubits cannot exceed physical_qubits.")
    if not isinstance(layout, Sequence) or isinstance(layout, (str, bytes)):
        raise ValidationError("layout must be a sequence of physical-qubit indices.")
    if len(layout) != logical_qubits:
        raise ValidationError("layout length must equal logical_qubits.")
    normalized = []
    for index, physical in enumerate(layout):
        validate_qubit(f"layout[{index}]", physical, physical_qubits)
        normalized.append(int(physical))
    if len(set(normalized)) != len(normalized):
        raise ValidationError("layout must map logical qubits to distinct physical qubits.")
    return tuple(normalized)


def embed_logical_state(
    logical_state: np.ndarray,
    logical_qubits: int,
    physical_qubits: int,
    layout: Sequence[int],
) -> np.ndarray:
    layout = validate_layout(layout, logical_qubits, physical_qubits)
    validate_statevector_size(logical_qubits)
    validate_statevector_size(physical_qubits)
    logical_state = np.asarray(logical_state)
    if logical_state.ndim != 1 or logical_state.size != (1 << logical_qubits):
        raise ValidationError("logical_state shape does not match logical_qubits.")
    if not np.iscomplexobj(logical_state):
        raise ValidationError("logical_state must use a complex dtype.")
    physical_state = np.zeros(1 << physical_qubits, dtype=complex)
    for logical_index, amplitude in enumerate(logical_state):
        physical_index = 0
        for logical_qubit, physical_qubit in enumerate(layout):
            bit = (logical_index >> (logical_qubits - 1 - logical_qubit)) & 1
            if bit:
                physical_index |= 1 << (physical_qubits - 1 - physical_qubit)
        physical_state[physical_index] = amplitude
    norm = float(np.linalg.norm(physical_state))
    if not np.isfinite(norm) or norm <= 0.0:
        raise ValidationError("Embedded physical state is invalid.")
    return physical_state / norm


def compile_source_workload(
    gates: Sequence[Gate],
    processor: PracticeProcessor,
    layout: Sequence[int],
) -> list[Gate]:
    if not gates:
        raise ValidationError("The logical workload cannot be empty.")
    logical_qubits = max(max(g.qubits) for g in gates) + 1
    layout = validate_layout(layout, logical_qubits, processor.num_qubits)
    compiled: list[Gate] = []

    for index, gate in enumerate(gates):
        if not isinstance(gate, Gate):
            raise ValidationError(f"gates[{index}] must be a Gate instance.")
        mapped = tuple(layout[q] for q in gate.qubits)
        mapped_gate = Gate(gate.name, mapped, theta=gate.theta, role=gate.role)

        if len(mapped) == 1:
            compiled.append(mapped_gate)
            continue

        q0, q1 = mapped
        direct = (q0, q1) in processor.coupling_map or (q1, q0) in processor.coupling_map
        if direct:
            compiled.append(mapped_gate)
            continue

        path = shortest_path(
            processor.coupling_map,
            processor.num_qubits,
            q0,
            q1,
        )
        forward_pairs = list(zip(path[:-2], path[1:-1]))
        for a, b in forward_pairs:
            compiled.extend(
                (
                    Gate("cx", (a, b), role="routing"),
                    Gate("cx", (b, a), role="routing"),
                    Gate("cx", (a, b), role="routing"),
                )
            )
        compiled.append(
            Gate(
                gate.name,
                (path[-2], path[-1]),
                theta=gate.theta,
                role=gate.role,
            )
        )
        for a, b in reversed(forward_pairs):
            compiled.extend(
                (
                    Gate("cx", (a, b), role="routing"),
                    Gate("cx", (b, a), role="routing"),
                    Gate("cx", (a, b), role="routing"),
                )
            )
    return compiled


def _noise_rates(definition: dict) -> tuple[float, float, float]:
    noise = definition.get("noise")
    if not isinstance(noise, dict):
        raise ValidationError("Source processor is missing its noise object.")
    p1 = noise.get("single_qubit_error", noise.get("p1"))
    p2 = noise.get("two_qubit_error", noise.get("p2"))
    readout = noise.get("readout_error")
    if p1 is None or p2 is None or readout is None:
        raise ValidationError(
            "Source processor must define single-qubit, two-qubit and readout error rates."
        )
    return float(p1), float(p2), float(readout)


def _to_practice_processor(definition: dict) -> PracticeProcessor:
    p1, p2, readout = _noise_rates(definition)
    return PracticeProcessor(
        name=str(definition["name"]),
        num_qubits=int(definition["num_qubits"]),
        coupling_map=tuple(tuple(edge) for edge in definition["coupling_map"]),
        p1=p1,
        p2=p2,
        readout_error=readout,
    )


def benchmark_source_processor(
    processor: PracticeProcessor,
    logical_gates: Sequence[Gate],
    exact_logical_state: np.ndarray,
    logical_qubits: int,
    layout: Sequence[int],
    trajectories: int,
    seed: int,
) -> dict[str, float]:
    positive_int("trajectories", trajectories, maximum=MAX_TRAJECTORIES)
    nonnegative_int("seed", seed)
    layout = validate_layout(layout, logical_qubits, processor.num_qubits)

    physical_exact_state = embed_logical_state(
        exact_logical_state,
        logical_qubits,
        processor.num_qubits,
        layout,
    )
    compiled = compile_source_workload(logical_gates, processor, layout)

    rng = np.random.default_rng(seed)
    count = 0
    fidelity_mean = fidelity_m2 = 0.0
    z_mean = z_m2 = 0.0
    measured_z_mean = measured_z_m2 = 0.0

    for _ in range(trajectories):
        state = _simulate_noisy_trajectory(
            compiled,
            processor,
            processor.num_qubits,
            rng,
        )
        fidelity = float(
            np.clip(np.abs(np.vdot(physical_exact_state, state)) ** 2, 0.0, 1.0)
        )
        physical_measurement_qubit = layout[0]
        z0 = _z_expectation(
            state,
            physical_measurement_qubit,
            processor.num_qubits,
        )
        measured_z0 = (1.0 - 2.0 * processor.readout_error) * z0

        count, fidelity_mean, fidelity_m2 = _online_update(
            count, fidelity_mean, fidelity_m2, fidelity
        )
        _, z_mean, z_m2 = _online_update(count - 1, z_mean, z_m2, z0)
        _, measured_z_mean, measured_z_m2 = _online_update(
            count - 1,
            measured_z_mean,
            measured_z_m2,
            measured_z0,
        )

    divisor = max(count - 1, 1)
    fidelity_std = (
        float(np.sqrt(max(fidelity_m2 / divisor, 0.0)))
        if count > 1
        else 0.0
    )
    z_std = float(np.sqrt(max(z_m2 / divisor, 0.0))) if count > 1 else 0.0
    measured_z_std = (
        float(np.sqrt(max(measured_z_m2 / divisor, 0.0)))
        if count > 1
        else 0.0
    )

    metrics = count_metrics(compiled, processor.num_qubits)
    p1, p2, readout = _noise_rates(
        {
            "noise": {
                "single_qubit_error": processor.p1,
                "two_qubit_error": processor.p2,
                "readout_error": processor.readout_error,
            }
        }
    )
    metrics.update(
        {
            "logical_qubits": float(logical_qubits),
            "mean_fidelity": fidelity_mean,
            "fidelity_std": fidelity_std,
            "fidelity_stderr": fidelity_std / np.sqrt(count),
            "mean_z0_expectation": z_mean,
            "z0_expectation_std": z_std,
            "measured_z0_expectation": measured_z_mean,
            "measured_z0_expectation_std": measured_z_std,
            "trajectories": float(count),
            "seed": float(seed),
            "p1": p1,
            "p2": p2,
            "readout_error": readout,
        }
    )
    return metrics


def run_source_ab(
    config_path: str | Path = ROOT / "data" / "practice_config.json",
) -> pd.DataFrame:
    config_path = Path(config_path)
    cfg = json.loads(config_path.read_text(encoding="utf-8"))

    system = cfg["system"]
    logical_qubits = int(system["n_qubits"])
    trajectories = int(cfg["shots_or_trajectories"])
    seed = int(cfg["seed"])

    definitions: dict[str, dict] = {}
    processors: dict[str, PracticeProcessor] = {}
    noise_values: dict[str, tuple[float, float, float]] = {}
    for label in ("A", "B"):
        relative = cfg["processor_files"][label]
        definition = load_processor(
            ROOT / relative,
            require_source_document=True,
        )
        definitions[label] = definition
        processors[label] = _to_practice_processor(definition)
        noise_values[label] = _noise_rates(definition)

    if noise_values["A"] != noise_values["B"]:
        raise ValidationError(
            "Controlled A/B benchmark requires identical synthetic noise rates."
        )

    physical_qubits = max(processors["A"].num_qubits, processors["B"].num_qubits)
    layout = validate_layout(
        cfg["layout"],
        logical_qubits,
        physical_qubits,
    )

    logical = logical_trotter_circuit(
        int(system["trotter_steps"]),
        float(system["total_time"]),
        float(system["J"]),
        float(system["h"]),
        n_qubits=logical_qubits,
    )
    exact = ideal_exact_state(
        logical_qubits,
        float(system["total_time"]),
        float(system["J"]),
        float(system["h"]),
    )

    rows = []
    for label in ("A", "B"):
        if any(q >= processors[label].num_qubits for q in layout):
            raise ValidationError(
                f"Configured layout does not fit source Processor {label}."
            )
        result = benchmark_source_processor(
            processors[label],
            logical,
            exact,
            logical_qubits,
            layout,
            trajectories,
            seed,
        )
        result.update(
            {
                "processor": label,
                "processor_name": definitions[label]["name"],
                "processor_source": definitions[label]["source"],
            }
        )
        rows.append(result)

    frame = pd.DataFrame(rows).sort_values("processor").reset_index(drop=True)
    if list(frame["processor"]) != ["A", "B"]:
        raise RuntimeError("Source A/B benchmark must produce exactly Processor A and Processor B.")
    return frame
