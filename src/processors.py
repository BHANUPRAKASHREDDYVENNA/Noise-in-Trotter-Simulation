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


def load_processor(
    path: str | Path,
    *,
    require_official_source: bool = False,
) -> dict[str, Any]:
    path = Path(path)
    if not path.is_file():
        raise FileNotFoundError(f"Processor definition not found: {path}")
    try:
        processor = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValidationError(f"Invalid JSON in {path}: {exc}") from exc
    validate_processor_definition(
        processor,
        path.name,
        require_official_source=require_official_source,
    )
    return processor


def validate_processor_definition(
    processor: dict[str, Any],
    label: str,
    *,
    require_official_source: bool = False,
) -> None:
    validate_processor_mapping_dict(processor, label)
    noise = processor.get("noise") or {}
    for key in ("p1", "p2", "readout_error"):
        if key in noise:
            probability(f"{label}.noise.{key}", noise[key])

    if require_official_source and processor.get("source") != "official_challenge_kit":
        raise ValidationError(
            f"{label} must declare source=official_challenge_kit for official validation."
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
