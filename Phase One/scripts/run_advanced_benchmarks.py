#!/usr/bin/env python3
"""Run the complete next-level optimization study and export comparative tables."""

from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.advanced_optimization import run_advanced_optimization_suite
from src.processor_d_designer import compare_all_architectures


def main() -> None:
    print("=" * 70)
    print("Executing Next-Level S3 Architecture & Optimization Benchmark Suite")
    print("=" * 70)

    tables_dir = ROOT / "results" / "tables"
    tables_dir.mkdir(parents=True, exist_ok=True)

    # 1. Advanced optimization suite
    print("\n[1/3] Running Geometry-Aware Layout, 2nd-Order Trotter, and ZNE studies...")
    results = run_advanced_optimization_suite(
        processor_A_path=str(ROOT / "processors" / "processor_A.json"),
        processor_B_path=str(ROOT / "processors" / "processor_B.json"),
        trajectories=1000,
        seed=2026,
    )

    df_layout = results["layout_comparison"]
    df_trotter = results["trotter_scaling"]
    zne_summary = results["zne_summary"]

    df_layout.to_csv(tables_dir / "advanced_layout_optimization.csv", index=False)
    df_trotter.to_csv(tables_dir / "advanced_trotter_scaling.csv", index=False)

    df_zne = pd.DataFrame([zne_summary])
    df_zne.to_csv(tables_dir / "advanced_zne_mitigation.csv", index=False)

    print("\n--- Layout Optimization Summary ---")
    print(df_layout.to_string(index=False))

    print("\n--- 1st vs 2nd-Order Trotter Algorithmic Error Scaling ---")
    print(df_trotter.to_string(index=False))

    print("\n--- Zero-Noise Extrapolation (ZNE) Expectation Recovery ---")
    for k, v in zne_summary.items():
        print(f"  {k}: {v}")

    # 2. Processor D Design & Bell benchmark
    print("\n[2/3] Comparing Topological Properties and Port Entanglement across A, B, and D...")
    df_graphs, df_bell = compare_all_architectures(ROOT)

    df_graphs.to_csv(tables_dir / "advanced_graph_metrics.csv", index=False)
    df_bell.to_csv(tables_dir / "advanced_bell_port_comparison.csv", index=False)

    print("\n--- Topological Graph Metrics ---")
    print(df_graphs.to_string(index=False))

    print("\n--- Bell Port Verification & Entanglement Correlation ---")
    print(df_bell.to_string(index=False))

    print("\n[3/3] All advanced benchmark tables written to results/tables/ successfully.")
    print("=" * 70)


if __name__ == "__main__":
    main()
