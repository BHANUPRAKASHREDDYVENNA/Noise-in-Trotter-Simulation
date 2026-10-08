from __future__ import annotations

import argparse
from pathlib import Path
import json

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


def validate(practice: bool = False) -> None:
    missing = [p for p in BASE_REQUIRED if not (ROOT / p).exists()]
    if missing:
        raise SystemExit("Missing required files:\n- " + "\n- ".join(missing))

    spec = json.loads(
        (ROOT / "data" / "guide_settings.json").read_text(encoding="utf-8")
    )
    if spec["problem_statement"]["code"] != "S3":
        raise SystemExit("Selected problem statement is not S3.")

    expected = [
        "scripts/run_practice.py",
        "scripts/run_bell_benchmark.py",
        "scripts/make_practice_figures.py",
        "tests/test_practice.py",
        "tests/test_bell_benchmark.py",
    ]
    missing = [p for p in expected if not (ROOT / p).exists()]
    if missing:
        raise SystemExit("Missing workflow/test files:\n- " + "\n- ".join(missing))

    if practice:
        print("Practice-mode repository validation passed.")
    else:
        print("Guide-derived Phase 1 repository structure passed static checks.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--practice", action="store_true")
    args = parser.parse_args()
    validate(practice=args.practice)
