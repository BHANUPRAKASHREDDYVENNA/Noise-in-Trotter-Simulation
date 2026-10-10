from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

BASE_REQUIRED = [
    "README.md",
    "main.ipynb",
    "requirements.txt",
    "data/guide_settings.json",
    "processors/processor_A.json",
    "processors/processor_B.json",
    "src/problem.py",
    "src/processors.py",
    "src/routing.py",
    "src/metrics.py",
    "src/visualization.py",
    "src/bell_benchmark.py",
    "src/practice_s3.py",
    "report/report.md",
]

WORKFLOW_FILES = [
    "scripts/run_practice.py",
    "scripts/run_bell_benchmark.py",
    "scripts/make_practice_figures.py",
    "scripts/security_audit.py",
    "tests/test_practice.py",
    "tests/test_bell_benchmark.py",
    "scripts/verify_notebook.py",
]


def _load_json(path: str | Path) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _safe_repo_path(relative_path: str) -> Path:
    if not isinstance(relative_path, str) or not relative_path.strip():
        raise SystemExit("Manifest paths must be non-empty strings.")
    candidate = (ROOT / relative_path).resolve()
    if ROOT != candidate and ROOT not in candidate.parents:
        raise SystemExit(f"Manifest path escapes the repository: {relative_path}")
    return candidate


def _check_base() -> None:
    missing = [p for p in BASE_REQUIRED if not (ROOT / p).exists()]
    if missing:
        raise SystemExit("Missing required files:\n- " + "\n- ".join(missing))

    spec = _load_json("data/guide_settings.json")
    if spec.get("problem_statement", {}).get("code") != "S3":
        raise SystemExit("Selected problem statement is not S3.")

    missing = [p for p in WORKFLOW_FILES if not (ROOT / p).exists()]
    if missing:
        raise SystemExit("Missing workflow/test files:\n- " + "\n- ".join(missing))


def _check_practice_results() -> None:
    comparison = ROOT / "results" / "tables" / "practice_ab_comparison.csv"
    if not comparison.is_file():
        raise SystemExit("Practice result table is missing. Run scripts/run_practice.py first.")

    with comparison.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    if {row.get("processor") for row in rows} != {"A", "B"}:
        raise SystemExit("Practice results must contain exactly Processor A and Processor B.")

    for row in rows:
        fidelity = float(row["mean_fidelity"])
        depth = float(row["depth"])
        two_q = float(row["two_qubit_gate_count"])
        if not 0.0 <= fidelity <= 1.0:
            raise SystemExit("Practice mean_fidelity must be in [0, 1].")
        if not all(math.isfinite(value) and value >= 0.0 for value in (depth, two_q)):
            raise SystemExit("Practice architecture metrics must be finite and non-negative.")

    figures = ROOT / "results" / "figures"
    required_figures = {"practice_ab_performance.png", "practice_architecture_tradeoffs.png"}
    missing_figures = [name for name in required_figures if not (figures / name).is_file()]
    if missing_figures:
        raise SystemExit("Missing practice figures:\n- " + "\n- ".join(missing_figures))


def validate_practice() -> None:
    _check_base()
    _check_practice_results()
    print("Practice-mode repository validation passed.")


def validate_official() -> None:
    _check_base()

    manifest_path = ROOT / "data" / "official_kit" / "manifest.json"
    if not manifest_path.exists():
        raise SystemExit("Official validation blocked: the organizer-supplied S3 Challenge Kit is missing.")

    manifest = _load_json(manifest_path)
    fields = ("kit_version", "source_files", "s3_instance", "processor_A", "processor_B", "required_outputs")
    missing = [key for key in fields if not manifest.get(key)]
    if missing:
        raise SystemExit("Official manifest is incomplete: " + ", ".join(missing))

    for source in manifest["source_files"]:
        if not _safe_repo_path(source).is_file():
            raise SystemExit(f"Official manifest references missing source file: {source}")

    for key in ("s3_instance", "processor_A", "processor_B"):
        if not _safe_repo_path(str(manifest[key])).is_file():
            raise SystemExit(f"Official manifest references missing file: {manifest[key]}")

    if not all(isinstance(item, str) and item.strip() for item in manifest["required_outputs"]):
        raise SystemExit("Official required_outputs must be non-empty strings.")

    spec = _load_json("data/guide_settings.json")
    if spec.get("status") != "OFFICIAL_CHALLENGE_KIT":
        raise SystemExit("Official validation blocked: guide-derived settings are still active.")

    for label in ("A", "B"):
        processor = _load_json(f"processors/processor_{label}.json")
        if processor.get("source") != "official_challenge_kit":
            raise SystemExit(f"Processor {label} is not marked as organizer-supplied.")
        text = json.dumps(processor).lower()
        if any(word in text for word in ("illustrative", "toy", "practice", "placeholder")):
            raise SystemExit(f"Processor {label} contains an illustrative configuration marker.")

    print("Official Phase-1 repository validation passed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--practice", action="store_true")
    group.add_argument("--official", action="store_true")
    args = parser.parse_args()
    validate_practice() if args.practice else validate_official()
