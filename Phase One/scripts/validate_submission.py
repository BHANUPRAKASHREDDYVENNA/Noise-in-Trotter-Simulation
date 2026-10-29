#!/usr/bin/env python3
"""Validate the repository against the supplied source document only."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

REQUIRED_FILES = (
    "README.md",
    "LICENSE",
    "main.ipynb",
    "requirements.txt",
    "requirements-practice.txt",
    "pyproject.toml",
    "docs/source_document.md",
    "docs/phase1_scope.md",
    "docs/pdf_requirements_matrix.md",
    "processors/processor_A.json",
    "processors/processor_B.json",
    "src/problem.py",
    "src/processors.py",
    "src/routing.py",
    "src/metrics.py",
    "src/visualization.py",
    "src/bell_benchmark.py",
    "src/practice_s3.py",
    "src/online_ab.py",
    "scripts/build_notebook.py",
    "scripts/run_practice.py",
    "scripts/make_practice_figures.py",
    "scripts/validate_submission.py",
    "tests/test_practice.py",
    "tests/test_validation.py",
    "tests/test_bell_benchmark.py",
    "tests/test_online_ab.py",
)


def _reject_duplicate_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json(path: str) -> dict:
    target = ROOT / path
    try:
        value = json.loads(
            target.read_text(encoding="utf-8"),
            object_pairs_hook=_reject_duplicate_pairs,
        )
    except FileNotFoundError as exc:
        raise SystemExit(f"missing JSON file: {path}") from exc
    except (json.JSONDecodeError, ValueError) as exc:
        raise SystemExit(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return value


def check_files() -> None:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        raise SystemExit("missing required files:\n- " + "\n- ".join(missing))


def check_processors() -> dict[str, dict]:
    expected = {
        "A": {
            "name": "processor_A",
            "num_qubits": 5,
            "architecture": "fixed baseline graph",
            "coupling_map": [[0, 1], [0, 2], [0, 3], [3, 4]],
        },
        "B": {
            "name": "processor_B",
            "num_qubits": 7,
            "architecture": "heavy-hex-inspired graph",
            "coupling_map": [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 0], [2, 6]],
        },
    }

    definitions = {}
    for label, contract in expected.items():
        data = load_json(f"processors/processor_{label}.json")
        definitions[label] = data
        for key, value in contract.items():
            if data.get(key) != value:
                raise SystemExit(
                    f"Processor {label} violates source-document contract for {key}."
                )
        if data.get("stage") != "online":
            raise SystemExit(f"Processor {label} must be online.")
        if data.get("source") != "source_document":
            raise SystemExit(f"Processor {label} must identify source_document as its source.")

        noise = data.get("noise")
        if not isinstance(noise, dict):
            raise SystemExit(f"Processor {label} noise configuration is missing.")
        required_noise = ("single_qubit_error", "two_qubit_error", "readout_error")
        for key in required_noise:
            if key not in noise:
                raise SystemExit(f"Processor {label} is missing noise.{key}.")
            value = float(noise[key])
            if not math.isfinite(value) or not 0 <= value < 1:
                raise SystemExit(f"Processor {label} has invalid {key}.")

    if definitions["A"]["noise"] != definitions["B"]["noise"]:
        raise SystemExit("Controlled A/B benchmark requires identical synthetic noise rates.")

    return definitions


def check_config(definitions: dict[str, dict]) -> dict:
    cfg = load_json("data/practice_config.json")
    if cfg.get("processor_files") != {
        "A": "processors/processor_A.json",
        "B": "processors/processor_B.json",
    }:
        raise SystemExit("practice_config must point directly to source Processor A and B JSON files.")
    if cfg.get("layout") != [0, 1, 2]:
        raise SystemExit("practice_config must use the documented deterministic logical-to-physical layout.")
    system = cfg.get("system", {})
    if system.get("n_qubits") != 3:
        raise SystemExit("The illustrative S3 workload must use the documented 3 logical qubits.")
    if int(cfg.get("shots_or_trajectories", 0)) != 2000:
        raise SystemExit("The controlled benchmark must use 2000 trajectories.")
    if not isinstance(cfg.get("seed"), int) or cfg["seed"] < 0:
        raise SystemExit("The controlled benchmark seed must be a non-negative integer.")
    return cfg


def check_notebook() -> None:
    notebook = load_json("main.ipynb")
    text = "\n".join("".join(cell.get("source", [])) for cell in notebook.get("cells", []))
    required = (
        "S3",
        "Processor A",
        "Processor B",
        "processors/processor_A.json",
        "processors/processor_B.json",
        "fixed baseline graph",
        "heavy-hex-inspired graph",
        "Depth",
        "SWAP",
        "physical qubits",
        "run_benchmark",
    )
    normalized = text.casefold()
    missing = [term for term in required if term.casefold() not in normalized]
    if missing:
        raise SystemExit(
            "notebook is missing required source-document concepts: " + ", ".join(missing)
        )
    forbidden = (
        "official_challenge_kit",
        "practice_fully_connected_3q",
        "practice_line_3q",
    )
    for marker in forbidden:
        if marker in text.casefold():
            raise SystemExit(f"notebook contains a stale or unsupported marker: {marker}")


def check_results(require_generated: bool, definitions: dict[str, dict], cfg: dict) -> None:
    if not require_generated:
        return
    table = ROOT / "results" / "tables" / "practice_ab_comparison.csv"
    if not table.is_file():
        raise SystemExit("no generated source A/B result table is present.")

    with table.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 2:
        raise SystemExit("generated A/B result table must contain exactly two processor rows.")

    by_label = {row.get("processor"): row for row in rows}
    if set(by_label) != {"A", "B"}:
        raise SystemExit("generated A/B result table must contain Processor A and Processor B.")

    expected_swaps = {"A": 0.0, "B": 8.0}
    expected_2q = {"A": 4.0, "B": 28.0}
    serialized_float_tolerance = 5e-7
    # Re-run the benchmark and compare against the saved table. This closes the
    # provenance loophole where a manually edited CSV could otherwise pass schema checks.
    try:
        from src.online_ab import run_source_ab
        import pandas as pd
        fresh = run_source_ab(cfg.get("config_path", ROOT / "data" / "practice_config.json"))
        saved = pd.DataFrame(rows)
        saved = saved.sort_values("processor").reset_index(drop=True)
        fresh = fresh.sort_values("processor").reset_index(drop=True)
        for column in fresh.columns:
            if column not in saved.columns:
                raise SystemExit(f"Generated result table is missing benchmark column: {column}")
            if fresh[column].dtype.kind in "biufc" and saved[column].dtype.kind in "biufc":
                for expected_value, saved_value in zip(fresh[column], saved[column]):
                    if not math.isclose(
                            float(expected_value),
                            float(saved_value),
                            rel_tol=0,
                            abs_tol=serialized_float_tolerance,
                        ):
                        raise SystemExit(f"Saved benchmark result differs from a fresh source A/B run in {column}.")
            elif not fresh[column].astype(str).equals(saved[column].astype(str)):
                raise SystemExit(f"Saved benchmark result differs from a fresh source A/B run in {column}.")
    except Exception as exc:
        if isinstance(exc, SystemExit):
            raise
        raise SystemExit(f"Fresh source A/B benchmark verification failed: {exc}") from exc

    for label in ("A", "B"):
        row = by_label[label]
        data = definitions[label]

        if row.get("processor_name") != data["name"]:
            raise SystemExit(f"Result row {label} does not identify the source processor.")
        if row.get("processor_source") != "source_document":
            raise SystemExit(f"Result row {label} does not identify source_document provenance.")
        if row.get("compilation_baseline") != data.get("compilation_baseline"):
            raise SystemExit(f"Result row {label} has the wrong compilation baseline metadata.")
        if float(row["physical_qubits"]) != float(data["num_qubits"]):
            raise SystemExit(f"Result row {label} has the wrong physical-qubit count.")
        if float(row["logical_qubits"]) != float(cfg["system"]["n_qubits"]):
            raise SystemExit(f"Result row {label} has the wrong logical-qubit count.")
        if int(float(row["seed"])) != int(cfg["seed"]):
            raise SystemExit(f"Result row {label} does not use the common benchmark seed.")
        if int(float(row["trajectories"])) != int(cfg["shots_or_trajectories"]):
            raise SystemExit(f"Result row {label} has the wrong trajectory count.")
        for field, noise_key in (
            ("p1", "single_qubit_error"),
            ("p2", "two_qubit_error"),
            ("readout_error", "readout_error"),
        ):
            if not math.isclose(
                float(row[field]),
                float(data["noise"][noise_key]),
                rel_tol=0,
                abs_tol=1e-15,
            ):
                raise SystemExit(f"Result row {label} has a noise mismatch in {field}.")

        if float(row["swap_count"]) != expected_swaps[label]:
            raise SystemExit(f"Result row {label} has unexpected routing/SWAP overhead.")
        if float(row["two_qubit_gate_count"]) != expected_2q[label]:
            raise SystemExit(f"Result row {label} has unexpected two-qubit gate count.")
        if float(row["routing_two_qubit_gate_count"]) != 3.0 * float(row["swap_count"]):
            raise SystemExit(f"Result row {label} has inconsistent SWAP gate accounting.")

        for name, value in row.items():
            if name in {"processor", "processor_name", "processor_source", "compilation_baseline"}:
                continue
            numeric = float(value)
            if not math.isfinite(numeric):
                raise SystemExit(f"non-finite generated metric: {name}")


def check_generated_figures(require_generated: bool) -> None:
    if not require_generated:
        return
    expected = {
        "A": "fixed baseline graph",
        "B": "heavy-hex-inspired graph",
    }
    for label, architecture in expected.items():
        path = ROOT / "results" / "figures" / f"processor_{label}_graph.svg"
        if not path.is_file():
            raise SystemExit(f"missing generated architecture figure: {path.name}")
        text = path.read_text(encoding="utf-8")
        if architecture not in text:
            raise SystemExit(f"{path.name} does not reflect the current processor architecture.")
        if label == "A" and "Fully Connected" in text:
            raise SystemExit("stale Processor A architecture figure detected.")
        if label == "B" and "5Q Line" in text:
            raise SystemExit("stale Processor B architecture figure detected.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--practice", action="store_true", help="require generated A/B result artifacts")
    args = parser.parse_args()

    check_files()
    definitions = check_processors()
    cfg = check_config(definitions)
    check_notebook()
    check_results(args.practice, definitions, cfg)
    check_generated_figures(args.practice)
    print("Repository validation: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
