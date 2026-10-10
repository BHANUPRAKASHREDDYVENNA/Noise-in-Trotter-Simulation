from __future__ import annotations

from typing import Any

from src.processors import validate_processor_definition


def transpile_for_processor(
    logical_circuit: Any,
    processor: dict,
    *,
    optimization_level: int = 1,
    seed_transpiler: int = 2026,
):
    validate_processor_definition(processor, "processor")
    if not isinstance(optimization_level, int) or not 0 <= optimization_level <= 3:
        raise ValueError("optimization_level must be an integer from 0 to 3.")
    if isinstance(seed_transpiler, bool) or not isinstance(seed_transpiler, int):
        raise ValueError("seed_transpiler must be an integer.")

    try:
        from qiskit import transpile
        from qiskit.transpiler import CouplingMap
    except ImportError as exc:
        raise RuntimeError(
            "Qiskit is not installed. Install requirements.txt or the organizer-supplied environment."
        ) from exc

    coupling_map = CouplingMap(processor["coupling_map"])
    return transpile(
        logical_circuit,
        coupling_map=coupling_map,
        basis_gates=processor.get("basis_gates") or None,
        optimization_level=optimization_level,
        seed_transpiler=seed_transpiler,
    )
