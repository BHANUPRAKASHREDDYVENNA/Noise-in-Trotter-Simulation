from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

BASE_REQUIRED = [
    "README.md",
    "LICENSE",
    "SECURITY.md",
    "main.ipynb",
    "requirements.txt",
    "requirements-practice.txt",
    "pyproject.toml",
    "data/guide_settings.json",
    "data/practice_config.json",
    "data/official_kit/manifest.schema.json",
    "processors/processor_A.json",
    "processors/processor_B.json",
    "src/problem.py",
    "src/processors.py",
    "src/routing.py",
    "src/metrics.py",
    "src/visualization.py",
    "src/bell_benchmark.py",
    "src/practice_s3.py",
    "src/validation.py",
    "report/report.md",
    "requirements-ci.lock",
    "requirements-quality.txt",
]

WORKFLOW_FILES = [
    ".github/workflows/ci.yml",
    "scripts/build_notebook.py",
    "scripts/run_practice.py",
    "scripts/make_practice_figures.py",
    "scripts/security_audit.py",
    "scripts/verify_notebook.py",
    "scripts/release_gate.py",
    "tests/test_practice.py",
    "tests/test_validation.py",
    "tests/test_bell_benchmark.py",
    "tests/test_metrics.py",
]


def _load_json(path: str | Path) -> dict[str, Any]:
    target = ROOT / path
    try:
        data = json.loads(target.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"Required JSON file is missing: {path}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON in {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit(f"JSON file must contain an object: {path}")
    return data


def _safe_repo_path(relative_path: str) -> Path:
    if not isinstance(relative_path, str) or not relative_path.strip():
        raise SystemExit("Manifest paths must be non-empty strings.")
    candidate = (ROOT / relative_path).resolve()
    if ROOT != candidate and ROOT not in candidate.parents:
        raise SystemExit(f"Manifest path escapes the repository: {relative_path}")
    return candidate


def _check_base() -> None:
    missing = [p for p in BASE_REQUIRED if not (ROOT / p).is_file()]
    if missing:
        raise SystemExit("Missing required files:\n- " + "\n- ".join(missing))

    spec = _load_json("data/guide_settings.json")
    if spec.get("problem_statement", {}).get("code") != "S3":
        raise SystemExit("Selected problem statement is not S3.")

    workflow_missing = [p for p in WORKFLOW_FILES if not (ROOT / p).is_file()]
    if workflow_missing:
        raise SystemExit("Missing workflow/test files:\n- " + "\n- ".join(workflow_missing))


def _check_practice_results() -> None:
    comparison = ROOT / "results" / "tables" / "practice_ab_comparison.csv"
    if not comparison.is_file():
        raise SystemExit("Practice result table is missing. Run scripts/run_practice.py first.")

    with comparison.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
        columns = set(reader.fieldnames or [])

    processors = [row.get("processor") for row in rows]
    if len(rows) != 2 or processors != ["A", "B"]:
        raise SystemExit("Practice results must contain exactly one row for Processor A and one for Processor B.")

    required_columns = {
        "processor",
        "mean_fidelity",
        "depth",
        "two_qubit_gate_count",
        "swap_count",
        "physical_qubits",
        "trajectories",
        "fidelity_stderr",
    }
    if not required_columns.issubset(columns):
        raise SystemExit(
            "Practice result table is missing required architecture or uncertainty columns: "
            + ", ".join(sorted(required_columns - columns))
        )

    for row in rows:
        try:
            fidelity = float(row["mean_fidelity"])
            numeric = [
                float(row["depth"]),
                float(row["two_qubit_gate_count"]),
                float(row["swap_count"]),
                float(row["physical_qubits"]),
                float(row["trajectories"]),
                float(row["fidelity_stderr"]),
            ]
        except (KeyError, TypeError, ValueError) as exc:
            raise SystemExit("Practice result table contains malformed numeric fields.") from exc

        if not math.isfinite(fidelity) or not 0.0 <= fidelity <= 1.0:
            raise SystemExit("Practice mean_fidelity must be finite and in [0, 1].")
        if not all(math.isfinite(value) and value >= 0.0 for value in numeric):
            raise SystemExit(
                "Practice architecture and uncertainty metrics must be finite and non-negative."
            )

    figures = ROOT / "results" / "figures"
    required_figures = {"practice_ab_performance.png", "practice_architecture_tradeoffs.png"}
    missing_figures = [name for name in required_figures if not (figures / name).is_file()]
    if missing_figures:
        raise SystemExit("Missing practice figures:\n- " + "\n- ".join(missing_figures))


def validate_practice() -> None:
    _check_base()
    _check_practice_results()
    print("Practice-mode repository validation passed.")


def _manifest_string(manifest: dict[str, Any], key: str) -> str:
    value = manifest.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(f"Official manifest field {key} must be a non-empty string.")
    return value


def validate_official() -> None:
    _check_base()

    manifest_path = ROOT / "data" / "official_kit" / "manifest.json"
    if not manifest_path.is_file():
        raise SystemExit(
            "Official validation blocked: the organizer-supplied S3 Challenge Kit is missing."
        )

    manifest = _load_json(manifest_path)
    _manifest_string(manifest, "kit_version")
    s3_instance_value = _manifest_string(manifest, "s3_instance")

    source_files = manifest.get("source_files")
    if not isinstance(source_files, list) or not source_files or not all(
        isinstance(item, str) and item.strip() for item in source_files
    ):
        raise SystemExit(
            "Official manifest source_files must be a non-empty list of paths."
        )

    required_outputs = manifest.get("required_outputs")
    if not isinstance(required_outputs, list) or not required_outputs or not all(
        isinstance(item, str) and item.strip() for item in required_outputs
    ):
        raise SystemExit(
            "Official manifest required_outputs must be a non-empty list of strings."
        )

    if manifest.get("processor_A") != "processors/processor_A.json":
        raise SystemExit(
            "Official manifest processor_A must reference processors/processor_A.json."
        )
    if manifest.get("processor_B") != "processors/processor_B.json":
        raise SystemExit(
            "Official manifest processor_B must reference processors/processor_B.json."
        )

    for source in source_files:
        if not _safe_repo_path(source).is_file():
            raise SystemExit(
                f"Official manifest references missing source file: {source}"
            )

    s3_instance = _safe_repo_path(s3_instance_value)
    if not s3_instance.is_file():
        raise SystemExit(
            f"Official manifest references missing S3 instance: {s3_instance_value}"
        )

    for label in ("A", "B"):
        processor = _load_json(f"processors/processor_{label}.json")
        if processor.get("source") != "official_challenge_kit":
            raise SystemExit(
                f"Processor {label} is not marked as organizer-supplied."
            )
        text = json.dumps(processor, sort_keys=True).lower()
        if any(
            word in text
            for word in ("illustrative", "toy", "practice", "placeholder")
        ):
            raise SystemExit(
                f"Processor {label} contains an illustrative configuration marker."
            )

    spec = _load_json("data/guide_settings.json")
    if spec.get("status") != "OFFICIAL_CHALLENGE_KIT":
        raise SystemExit(
            "Official validation blocked: guide-derived settings are still active."
        )
    if spec.get("problem_statement", {}).get("code") != "S3":
        raise SystemExit(
            "Official validation blocked: selected problem statement is not S3."
        )

    print("Official Phase-1 repository validation passed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--practice", action="store_true")
    group.add_argument("--official", action="store_true")
    args = parser.parse_args()
    validate_practice() if args.practice else validate_official()
