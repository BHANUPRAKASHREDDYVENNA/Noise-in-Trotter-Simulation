from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Any

from src.processors import validate_processor_definition

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = (
    "README.md",
    "LICENSE",
    "SECURITY.md",
    "pyproject.toml",
    "requirements.txt",
    "requirements-ci.lock",
    "requirements-quality.txt",
    "main.ipynb",
    "data/practice_config.json",
    "processors/processor_A.json",
    "processors/processor_B.json",
    "src/__init__.py",
    "src/problem.py",
    "src/processors.py",
    "src/routing.py",
    "src/metrics.py",
    "src/visualization.py",
    "src/bell_benchmark.py",
    "src/practice_s3.py",
    "src/validation.py",
    "scripts/build_notebook.py",
    "scripts/make_practice_figures.py",
    "scripts/run_practice.py",
    "scripts/security_audit.py",
    "scripts/release_gate.py",
    "tests/test_practice.py",
    "tests/test_validation.py",
    "tests/test_bell_benchmark.py",
    "tests/test_metrics.py",
)

GENERATED_RESULTS = (
    "results/tables/practice_ab_comparison.csv",
    "results/tables/practice_processor_A_metrics.csv",
    "results/tables/practice_processor_B_metrics.csv",
    "results/figures/practice_ab_performance.png",
    "results/figures/practice_architecture_tradeoffs.png",
)


def _load_json(path: str) -> dict[str, Any]:
    try:
        value = json.loads((ROOT / path).read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON file {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"JSON root must be an object: {path}")
    return value


def _finite_nonnegative(value: str, field: str) -> None:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise SystemExit(f"{field} is not numeric: {value}") from exc
    if not math.isfinite(number) or number < 0.0:
        raise SystemExit(f"{field} must be finite and non-negative: {value}")


def _check_files() -> None:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        raise SystemExit("Repository contract missing files:\n- " + "\n- ".join(missing))


def _check_configuration() -> None:
    config = _load_json("data/practice_config.json")
    system = config.get("system")
    processors = config.get("processors")
    if not isinstance(system, dict) or not isinstance(processors, dict):
        raise SystemExit("practice_config.json requires system and processors objects.")

    required_system = ("n_qubits", "J", "h", "total_time", "trotter_steps")
    missing = [key for key in required_system if key not in system]
    if missing:
        raise SystemExit("practice_config.json missing system keys: " + ", ".join(missing))

    for key in ("n_qubits", "trotter_steps"):
        value = system[key]
        if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
            raise SystemExit(f"system.{key} must be a positive integer.")
    for key in ("J", "h", "total_time"):
        try:
            value = float(system[key])
        except (TypeError, ValueError) as exc:
            raise SystemExit(f"system.{key} must be numeric.") from exc
        if not math.isfinite(value) or (key == "total_time" and value < 0):
            raise SystemExit(f"system.{key} has an invalid value.")

    trajectories = config.get("shots_or_trajectories")
    if isinstance(trajectories, bool) or not isinstance(trajectories, int) or trajectories <= 0:
        raise SystemExit("shots_or_trajectories must be a positive integer.")

    seed = config.get("seed")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        raise SystemExit("seed must be a non-negative integer.")

    if set(processors) != {"A", "B"}:
        raise SystemExit("practice_config.json must define exactly processors A and B.")

    for label in ("A", "B"):
        processor = processors[label]
        if not isinstance(processor, dict):
            raise SystemExit(f"Processor {label} configuration must be an object.")
        required = ("name", "coupling_map", "p1", "p2", "readout_error")
        missing = [key for key in required if key not in processor]
        if missing:
            raise SystemExit(f"Processor {label} missing keys: {', '.join(missing)}")
        coupling_map = processor["coupling_map"]
        if not isinstance(coupling_map, list):
            raise SystemExit(f"Processor {label} coupling_map must be a list.")
        for edge in coupling_map:
            if not isinstance(edge, list) or len(edge) != 2:
                raise SystemExit(f"Processor {label} contains an invalid coupling edge.")
        for key in ("p1", "p2", "readout_error"):
            value = float(processor[key])
            if not math.isfinite(value) or not 0.0 <= value <= 1.0:
                raise SystemExit(f"Processor {label}.{key} must be in [0, 1].")


def _check_processor_definitions() -> None:
    for label in ("A", "B"):
        definition = _load_json(f"processors/processor_{label}.json")
        validate_processor_definition(definition, f"processor_{label}")
        if not definition["name"].strip():
            raise SystemExit(f"Processor {label} has an empty name.")


def _check_results() -> None:
    comparison = ROOT / "results/tables/practice_ab_comparison.csv"
    if not comparison.is_file():
        raise SystemExit("Practice comparison result is missing.")

    with comparison.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        columns = set(reader.fieldnames or ())

    required = {
        "processor",
        "mean_fidelity",
        "fidelity_stderr",
        "depth",
        "two_qubit_gate_count",
        "swap_count",
        "physical_qubits",
        "trajectories",
    }
    if not required.issubset(columns):
        raise SystemExit(
            "Practice comparison is missing columns: "
            + ", ".join(sorted(required - columns))
        )
    if len(rows) != 2 or [row.get("processor") for row in rows] != ["A", "B"]:
        raise SystemExit("Practice comparison must contain exactly ordered A and B rows.")

    for row in rows:
        fidelity = float(row["mean_fidelity"])
        if not math.isfinite(fidelity) or not 0.0 <= fidelity <= 1.0:
            raise SystemExit("mean_fidelity must be finite and in [0, 1].")
        for field in required - {"processor", "mean_fidelity"}:
            _finite_nonnegative(row[field], field)

    for path in GENERATED_RESULTS:
        target = ROOT / path
        if not target.is_file() or target.stat().st_size == 0:
            raise SystemExit(f"Generated artifact is missing or empty: {path}")


def main() -> None:
    _check_files()
    _check_configuration()
    _check_processor_definitions()
    _check_results()
    print("Internal repository contract validation passed.")


if __name__ == "__main__":
    main()
