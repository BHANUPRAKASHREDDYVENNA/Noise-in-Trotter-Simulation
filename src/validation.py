from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from typing import Any

DEFAULT_MAX_STATEVECTOR_BYTES = 128 * 1024 * 1024
MAX_TRAJECTORIES = 1_000_000


class ValidationError(ValueError):
    """Raised when scientific or processor configuration is invalid."""


def finite_real(name: str, value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValidationError(f"{name} must be a real number.")
    value = float(value)
    if not math.isfinite(value):
        raise ValidationError(f"{name} must be finite.")
    return value


def positive_int(name: str, value: Any, *, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValidationError(f"{name} must be an integer.")
    if value <= 0:
        raise ValidationError(f"{name} must be positive.")
    if maximum is not None and value > maximum:
        raise ValidationError(f"{name} must be <= {maximum}.")
    return value


def probability(name: str, value: Any) -> float:
    value = finite_real(name, value)
    if not 0.0 <= value <= 1.0:
        raise ValidationError(f"{name} must be in [0, 1].")
    return value


def validate_qubit(name: str, q: Any, num_qubits: int) -> int:
    if isinstance(q, bool) or not isinstance(q, int):
        raise ValidationError(f"{name} must be an integer.")
    if q < 0 or q >= num_qubits:
        raise ValidationError(f"{name} must be in [0, {num_qubits - 1}].")
    return q


def estimate_statevector_bytes(num_qubits: int, dtype_bytes: int = 16) -> int:
    positive_int("num_qubits", num_qubits)
    positive_int("dtype_bytes", dtype_bytes)
    return dtype_bytes * (1 << num_qubits)


def validate_statevector_size(
    num_qubits: int,
    *,
    max_bytes: int = DEFAULT_MAX_STATEVECTOR_BYTES,
) -> None:
    positive_int("max_bytes", max_bytes)
    required = estimate_statevector_bytes(num_qubits)
    if required > max_bytes:
        raise ValidationError(
            "Requested statevector exceeds the configured memory guard: "
            f"{required} bytes > {max_bytes} bytes."
        )


def validate_trotter_parameters(
    *,
    n_qubits: int,
    steps: int,
    total_time: float,
    coupling: float,
    field: float,
    trajectories: int | None = None,
) -> None:
    positive_int("n_qubits", n_qubits)
    positive_int("trotter_steps", steps)
    total_time = finite_real("total_time", total_time)
    finite_real("J", coupling)
    finite_real("h", field)
    if total_time < 0.0:
        raise ValidationError("total_time must be non-negative.")
    if trajectories is not None:
        positive_int("trajectories", trajectories, maximum=MAX_TRAJECTORIES)


def validate_processor_mapping(
    coupling_map: Sequence[Sequence[int]],
    num_qubits: int,
) -> tuple[tuple[int, int], ...]:
    positive_int("num_qubits", num_qubits)
    if not isinstance(coupling_map, Sequence) or isinstance(coupling_map, (str, bytes)):
        raise ValidationError("coupling_map must be a sequence of edges.")

    normalized: list[tuple[int, int]] = []
    seen: set[tuple[int, int]] = set()
    for index, edge in enumerate(coupling_map):
        if not isinstance(edge, Sequence) or len(edge) != 2:
            raise ValidationError(
                f"coupling_map[{index}] must contain exactly two qubit indices."
            )
        a, b = edge
        validate_qubit(f"coupling_map[{index}][0]", a, num_qubits)
        validate_qubit(f"coupling_map[{index}][1]", b, num_qubits)
        if a == b:
            raise ValidationError(f"coupling_map[{index}] cannot self-connect.")
        pair = (int(a), int(b))
        reverse = (pair[1], pair[0])
        if pair in seen or reverse in seen:
            raise ValidationError(f"Duplicate coupling edge detected: {pair}.")
        seen.add(pair)
        normalized.append(pair)

    if not normalized:
        raise ValidationError("coupling_map must contain at least one edge.")
    return tuple(normalized)


def validate_processor_mapping_dict(
    processor: Mapping[str, Any],
    label: str,
) -> None:
    if not isinstance(processor, Mapping):
        raise ValidationError(f"{label} must be a JSON object.")

    required = ("name", "num_qubits", "coupling_map", "basis_gates")
    missing = [key for key in required if key not in processor]
    if missing:
        raise ValidationError(f"{label} is missing required fields: {missing}.")

    name = processor["name"]
    if not isinstance(name, str) or not name.strip():
        raise ValidationError(f"{label}.name must be a non-empty string.")

    num_qubits = positive_int(f"{label}.num_qubits", processor["num_qubits"])
    validate_processor_mapping(processor["coupling_map"], num_qubits)

    gates = processor["basis_gates"]
    if not isinstance(gates, Sequence) or isinstance(gates, (str, bytes)) or not gates:
        raise ValidationError(f"{label}.basis_gates must be a non-empty sequence.")
    if any(not isinstance(g, str) or not g.strip() for g in gates):
        raise ValidationError(f"{label}.basis_gates must contain non-empty strings.")

    ports = processor.get("ports")
    if ports is not None:
        if not isinstance(ports, Sequence) or len(ports) != 2:
            raise ValidationError(f"{label}.ports must contain exactly two qubit indices.")
        validate_qubit(f"{label}.ports[0]", ports[0], num_qubits)
        validate_qubit(f"{label}.ports[1]", ports[1], num_qubits)
        if ports[0] == ports[1]:
            raise ValidationError(f"{label}.ports must refer to distinct qubits.")

    noise = processor.get("noise")
    if noise is not None:
        if not isinstance(noise, Mapping):
            raise ValidationError(f"{label}.noise must be an object.")
        for key in ("p1", "p2", "readout_error"):
            if key in noise:
                probability(f"{label}.noise.{key}", noise[key])
