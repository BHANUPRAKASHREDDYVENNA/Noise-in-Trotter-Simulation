from __future__ import annotations

import argparse
import json
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
    "tests/test_practice.py",
    "tests/test_bell_benchmark.py",
]


def _load_json(path: str | Path) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def _check_base() -> None:
    missing = [p for p in BASE_REQUIRED if not (ROOT / p).exists()]
    if missing:
        raise SystemExit("Missing required files:
- " + "
- ".join(missing))

    spec = _load_json("data/guide_settings.json")
    if spec.get("problem_statement", {}).get("code") != "S3":
        raise SystemExit("Selected problem statement is not S3.")

    missing = [p for p in WORKFLOW_FILES if not (ROOT / p).exists()]
    if missing:
        raise SystemExit("Missing workflow/test files:
- " + "
- ".join(missing))


def validate_practice() -> None:
    _check_base()
    print("Practice-mode repository validation passed.")


def validate_official() -> None:
    _check_base()

    manifest_path = ROOT / "data" / "official_kit" / "manifest.json"
    if not manifest_path.exists():
        raise SystemExit(
            "Official validation blocked: data/official_kit/manifest.json is missing. "
            "Add the organizer-supplied S3 Challenge Kit, record its paths/version in the manifest, "
            "and replace the illustrative processor/model files before submission."
        )

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    required_fields = [
        "kit_version",
        "source_files",
        "s3_instance",
        "processor_A",
        "processor_B",
        "required_outputs",
    ]
    missing_fields = [k for k in required_fields if not manifest.get(k)]
    if missing_fields:
        raise SystemExit(
            "Official validation blocked: manifest is incomplete for fields: "
            + ", ".join(missing_fields)
        )

    missing_files = []
    for key in ["s3_instance", "processor_A", "processor_B"]:
        path = ROOT / str(manifest[key])
        if not path.exists():
            missing_files.append(str(manifest[key]))
    if missing_files:
        raise SystemExit(
            "Official validation blocked: manifest references missing files:
- "
            + "
- ".join(missing_files)
        )

    spec = _load_json("data/guide_settings.json")
    if spec.get("status") != "OFFICIAL_CHALLENGE_KIT":
        raise SystemExit(
            "Official validation blocked: data/guide_settings.json still uses guide-derived "
            "settings. Promote it only after applying the organizer's S3 Challenge Kit."
        )

    for label in ["A", "B"]:
        processor = _load_json(f"processors/processor_{label}.json")
        text = json.dumps(processor).lower()
        forbidden = ("illustrative", "toy", "practice", "placeholder")
        if any(word in text for word in forbidden):
            raise SystemExit(
                f"Official validation blocked: Processor {label} still contains "
                "illustrative/toy/practice/placeholder configuration."
            )
        if processor.get("source") != "official_challenge_kit":
            raise SystemExit(
                f"Official validation blocked: Processor {label} must declare "
                "source=official_challenge_kit."
            )

    print("Official Phase-1 repository validation passed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--practice", action="store_true")
    parser.add_argument("--official", action="store_true")
    args = parser.parse_args()

    if args.practice and args.official:
        parser.error("Use either --practice or --official, not both.")
    if args.practice:
        validate_practice()
    elif args.official:
        validate_official()
    else:
        parser.error("Choose --practice or --official.")
