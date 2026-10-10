from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GENERATED = (
    "main.ipynb",
    "results/tables/practice_ab_comparison.csv",
    "results/tables/practice_processor_A_metrics.csv",
    "results/tables/practice_processor_B_metrics.csv",
    "results/figures/practice_ab_performance.png",
    "results/figures/practice_architecture_tradeoffs.png",
)


def run(label: str, *args: str, cwd: Path = ROOT) -> None:
    print(f"[release-gate] {label}")
    subprocess.run(
        [str(arg) for arg in args],
        cwd=cwd,
        check=True,
        stdin=None,
    )


def assert_clean_generated_outputs() -> None:
    run("Verify generated artifacts", "git", "diff", "--exit-code", "--", *GENERATED)


def assert_clean_tree() -> None:
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "--untracked-files=normal"],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    if result.stdout.strip():
        raise SystemExit(
            "Release gate requires a clean worktree after regeneration:\n"
            + result.stdout
        )


def build_and_smoke_test_package() -> None:
    run("Build wheel and sdist", sys.executable, "-m", "build")
    wheels = sorted((ROOT / "dist").glob("*.whl"))
    if not wheels:
        raise SystemExit("Package build produced no wheel.")

    with tempfile.TemporaryDirectory(prefix="release-gate-") as tmp:
        temp_root = Path(tmp)
        run(
            "Install built wheel",
            sys.executable,
            "-m",
            "pip",
            "install",
            "--no-deps",
            "--force-reinstall",
            str(wheels[-1].resolve()),
        )
        run(
            "Smoke-test installed package",
            sys.executable,
            "-c",
            (
                "import src; "
                "from src.validation import ValidationError; "
                "assert ValidationError is not None"
            ),
            cwd=temp_root,
        )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict-git", action="store_true")
    args = parser.parse_args()

    run("Security audit", sys.executable, "scripts/security_audit.py")
    run(
        "Static analysis",
        sys.executable,
        "-m",
        "ruff",
        "check",
        "src",
        "scripts",
        "tests",
    )
    run("Compile", sys.executable, "-m", "compileall", "-q", "src", "scripts", "tests")
    run("Rebuild notebook", sys.executable, "scripts/build_notebook.py")
    run("Verify notebook", sys.executable, "scripts/verify_notebook.py")
    run("Collect tests", sys.executable, "-m", "pytest", "--collect-only", "-q")
    run(
        "Run tests",
        sys.executable,
        "-m",
        "pytest",
        "-q",
        "-ra",
        "--strict-config",
        "--strict-markers",
    )
    run("Run S3 practice benchmark", sys.executable, "scripts/run_practice.py")
    run("Generate practice figures", sys.executable, "scripts/make_practice_figures.py")
    run("Validate practice repository", sys.executable, "scripts/validate_submission.py", "--practice")
    run("Dependency vulnerability audit", sys.executable, "-m", "pip_audit")
    assert_clean_generated_outputs()

    if args.strict_git:
        assert_clean_tree()

    build_and_smoke_test_package()

    if args.strict_git:
        assert_clean_tree()

    print("Release gate passed.")


if __name__ == "__main__":
    main()
