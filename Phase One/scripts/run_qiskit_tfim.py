#!/usr/bin/env python3
"""Run the official PS-S3 4-Spin TFIM benchmark per Qiskit Fall Fest 2026 Phase 1 Master Guide."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.qiskit_s3_tfim import run_ps_s3_benchmark, generate_degradation_svg


def main() -> None:
    print("=" * 76)
    print("Executing Official PS-S3: 4-Spin TFIM Trotter Noise Benchmark")
    print("SRM University-AP Qiskit Fall Fest 2026 Phase 1 Master Guide Specification")
    print("=" * 76)

    tables_dir = ROOT / "results" / "tables"
    figures_dir = ROOT / "results" / "figures"
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    print("\n[1/3] Running Trotter evolution n in {1, 2, 4} with 4096 shots & depolarizing noise...")
    df = run_ps_s3_benchmark(
        trotter_steps=(1, 2, 4),
        total_time=2.0,
        J=1.0,
        g=1.0,
        shots=4096,
        seed=42,
    )

    csv_path = tables_dir / "qiskit_tfim_s3_benchmark.csv"
    df.to_csv(csv_path, index=False)
    print(f"Benchmark results saved to: {csv_path}")

    print("\n--- Summary Benchmark Results ---")
    print(df[["processor", "trotter_steps", "total_cx", "algorithmic_fidelity", "noisy_sim_z0", "noisy_abs_error"]].to_string(index=False))

    print("\n[2/3] Generating noise degradation visualization SVG...")
    svg_path = figures_dir / "qiskit_tfim_s3_degradation.svg"
    generate_degradation_svg(df, svg_path)
    print(f"Chart saved to: {svg_path}")

    print("\n[3/3] TFIM S3 Benchmark completed successfully.")
    print("=" * 76)


if __name__ == "__main__":
    main()
