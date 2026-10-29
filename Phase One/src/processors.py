from __future__ import annotations

import json
from collections import deque
from pathlib import Path
from typing import Any

from src.validation import (
    ValidationError,
    probability,
    validate_processor_mapping,
    validate_processor_mapping_dict,
    validate_qubit,
)


def _reject_duplicate_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValidationError(f"Duplicate JSON key detected: {key}")
        result[key] = value
    return result


def load_processor(
    path: str | Path,
    *,
    require_source_document: bool = False,
) -> dict[str, Any]:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Processor definition not found: {path}")
    try:
        processor = json.loads(
            path.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_pairs,
        )
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Invalid JSON in {path}: {exc}") from exc
    validate_processor_definition(
        processor,
        path.name,
        require_source_document=require_source_document,
    )
    return processor


def validate_processor_definition(
    processor: dict[str, Any],
    label: str,
    *,
    require_source_document: bool = False,
) -> None:
    validate_processor_mapping_dict(processor, label)
    coupling_map = processor["coupling_map"]
    num_qubits = int(processor["num_qubits"])

    if num_qubits > 1:
        adjacency = [[] for _ in range(num_qubits)]
        for a, b in coupling_map:
            adjacency[a].append(b)
            adjacency[b].append(a)
        seen = {0}
        queue = deque([0])
        while queue:
            node = queue.popleft()
            for neighbor in adjacency[node]:
                if neighbor not in seen:
                    seen.add(neighbor)
                    queue.append(neighbor)
        if len(seen) != num_qubits:
            raise ValidationError(f"{label}.coupling_map must define a connected processor graph.")

    noise = processor.get("noise")
    if noise is not None:
        if not isinstance(noise, dict):
            raise ValidationError(f"{label}.noise must be an object.")

        p1 = noise.get("p1", noise.get("single_qubit_error"))
        p2 = noise.get("p2", noise.get("two_qubit_error"))
        readout = noise.get("readout_error")
        if p1 is None or p2 is None or readout is None:
            raise ValidationError(
                f"{label}.noise must define single-qubit, two-qubit and readout error rates."
            )
        probability(f"{label}.noise.single_qubit_error", p1)
        probability(f"{label}.noise.two_qubit_error", p2)
        probability(f"{label}.noise.readout_error", readout)

        if require_source_document:
            for key in ("single_qubit_error", "two_qubit_error", "readout_error"):
                if key not in noise:
                    raise ValidationError(
                        f"{label}.noise.{key} is required for source-document validation."
                    )

    if require_source_document and processor.get("source") != "source_document":
        raise ValidationError(
            f"{label} must declare source=source_document for source-document validation."
        )


def undirected_adjacency(
    coupling_map: tuple[tuple[int, int], ...] | list[tuple[int, int]],
    num_qubits: int,
) -> list[list[int]]:
    edges = validate_processor_mapping(coupling_map, num_qubits)
    adjacency = [[] for _ in range(num_qubits)]
    for a, b in edges:
        adjacency[a].append(b)
        adjacency[b].append(a)
    for neighbors in adjacency:
        neighbors.sort()
    return adjacency


def shortest_path(
    coupling_map: tuple[tuple[int, int], ...] | list[tuple[int, int]],
    num_qubits: int,
    source: int,
    target: int,
) -> tuple[int, ...]:
    validate_qubit("source", source, num_qubits)
    validate_qubit("target", target, num_qubits)
    if source == target:
        return (source,)

    adjacency = undirected_adjacency(coupling_map, num_qubits)
    previous = [-1] * num_qubits
    previous[source] = source
    queue = deque([source])

    while queue:
        node = queue.popleft()
        for neighbor in adjacency[node]:
            if previous[neighbor] != -1:
                continue
            previous[neighbor] = node
            if neighbor == target:
                queue.clear()
                break
            queue.append(neighbor)

    if previous[target] == -1:
        raise ValidationError(
            f"No coupling-map path exists between qubits {source} and {target}."
        )

    path = [target]
    while path[-1] != source:
        path.append(previous[path[-1]])
    path.reverse()
    return tuple(path)


def interaction_swap_count(
    coupling_map: tuple[tuple[int, int], ...] | list[tuple[int, int]],
    num_qubits: int,
    q0: int,
    q1: int,
    *,
    restore_layout: bool = False,
) -> int:
    path = shortest_path(coupling_map, num_qubits, q0, q1)
    distance = len(path) - 1
    swaps = max(0, distance - 1)
    return swaps * (2 if restore_layout else 1)
