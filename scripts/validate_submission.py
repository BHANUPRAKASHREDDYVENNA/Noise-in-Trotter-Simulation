#!/usr/bin/env python3
"""Validate the repository against the supplied source document only."""

from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

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
    "scripts/build_notebook.py",
    "scripts/run_practice.py",
    "scripts/make_practice_figures.py",
    "scripts/validate_submission.py",
    "tests/test_practice.py",
    "tests/test_validation.py",
    "tests/test_bell_benchmark.py",
)

def load_json(path: str) -> dict:
    target = ROOT / path
    try:
        value = json.loads(target.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"missing JSON file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise SystemExit(f"expected JSON object: {path}")
    return value

def check_files() -> None:
    missing = [path for path in REQUIRED_FILES if not (ROOT / path).is_file()]
    if missing:
        raise SystemExit("missing required files:\n- " + "\n- ".join(missing))

def check_processors() -> None:
    expected = {
        "A": {"name": "processor_A", "num_qubits": 5, "architecture": "fixed baseline graph"},
        "B": {"name": "processor_B", "num_qubits": 7, "architecture": "heavy-hex-inspired graph"},
    }
    for label, contract in expected.items():
        data = load_json(f"processors/processor_{label}.json")
        for key, value in contract.items():
            if data.get(key) != value:
                raise SystemExit(f"Processor {label} violates source-document contract for {key}.")
        if data.get("stage") != "online":
            raise SystemExit(f"Processor {label} must be online.")
        if data.get("source") != "source_document":
            raise SystemExit(f"Processor {label} must identify source_document as its source.")
        noise = data.get("noise")
        if not isinstance(noise, dict):
            raise SystemExit(f"Processor {label} noise configuration is missing.")
        for key in ("single_qubit_error", "two_qubit_error", "readout_error"):
            value = float(noise[key])
            if not math.isfinite(value) or not 0 <= value < 1:
                raise SystemExit(f"Processor {label} has invalid {key}.")

def check_notebook() -> None:
    notebook = json.loads((ROOT / "main.ipynb").read_text(encoding="utf-8"))
    text = "\n".join("".join(cell.get("source", [])) for cell in notebook.get("cells", []))
    required = (
        "S3",
        "Processor A",
        "Processor B",
        "fixed baseline graph",
        "heavy-hex-inspired graph",
        "Depth",
        "SWAP",
        "physical qubits",
    )
    missing = [term for term in required if term not in text]
    if missing:
        raise SystemExit("notebook is missing required source-document concepts: " + ", ".join(missing))
    forbidden = ("official_challenge_kit", "Challenge Kit", "organizer-supplied", "third-party grader", "external validation harness")
    found = [term for term in forbidden if term.lower() in text.lower()]
    if found:
        raise SystemExit("notebook contains out-of-scope terminology: " + ", ".join(found))

def check_results(require_generated: bool) -> None:
    if not require_generated:
        return
    candidates = (
        ROOT / "results" / "tables" / "practice_ab_comparison.csv",
        ROOT / "results" / "tables" / "trotter_AB.csv",
    )
    table = next((path for path in candidates if path.is_file()), None)
    if table is None:
        raise SystemExit("no generated A/B result table is present.")
    with table.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    if len(rows) != 2:
        raise SystemExit("generated A/B result table must contain exactly two processor rows.")
    labels = {row.get("processor") for row in rows}
    if labels not in ({"A", "B"}, {"processor_A", "processor_B"}):
        raise SystemExit("generated A/B result table must contain Processor A and Processor B.")
    for row in rows:
        for name, value in row.items():
            if name in {"processor", "processor_name"} or value in ("", None):
                continue
            try:
                numeric = float(value)
            except ValueError:
                continue
            if not math.isfinite(numeric):
                raise SystemExit(f"non-finite generated metric: {name}")

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--practice", action="store_true", help="also require generated A/B result artifacts")
    args = parser.parse_args()
    check_files()
    check_processors()
    check_notebook()
    check_results(args.practice)
    print("Repository validation: PASS")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
