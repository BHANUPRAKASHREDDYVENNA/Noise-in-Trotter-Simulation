"""Qiskit-specific transpilation adapter for the official Phase-1 workflow."""
from __future__ import annotations


def transpile_for_processor(logical_circuit, processor: dict, optimization_level: int = 1):
    """Transpile a logical circuit using an organizer-supplied processor definition."""
    try:
        from qiskit import transpile
        from qiskit.transpiler import CouplingMap
    except ImportError as exc:  # pragma: no cover - exercised only in official setup
        raise RuntimeError(
            "Qiskit is not installed. Install the organizer-supplied environment."
        ) from exc

    coupling_map = CouplingMap(processor["coupling_map"])
    return transpile(
        logical_circuit,
        coupling_map=coupling_map,
        basis_gates=processor.get("basis_gates") or None,
        optimization_level=optimization_level,
    )
