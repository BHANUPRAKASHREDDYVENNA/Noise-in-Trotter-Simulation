from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pandas as pd

from src.bell_benchmark import ProcessorModel, benchmark_bell_processor

RESULTS = ROOT / "results" / "tables"
RESULTS.mkdir(parents=True, exist_ok=True)


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    a = load(ROOT / "processors" / "processor_A.json")
    b = load(ROOT / "processors" / "processor_B.json")

    models = [
        ProcessorModel(
            a["name"], a["num_qubits"], tuple(map(tuple, a["coupling_map"])),
            a["noise"]["p1"], a["noise"]["p2"], a["noise"]["readout_error"]
        ),
        ProcessorModel(
            b["name"], b["num_qubits"], tuple(map(tuple, b["coupling_map"])),
            b["noise"]["p1"], b["noise"]["p2"], b["noise"]["readout_error"]
        ),
    ]

    rows = []
    routing = [0, 0]
    routing[1] = 2

    for model, swaps in zip(models, routing):
        rows.append(benchmark_bell_processor(model, shots=2048, seed=7, routing_swaps=swaps))

    df = pd.DataFrame(rows)
    df.to_csv(RESULTS / "bell_processor_metrics.csv", index=False)

    arow, brow = df.iloc[0], df.iloc[1]
    comparison = pd.DataFrame([
        {"metric": "fidelity", "processor_A": arow["fidelity"], "processor_B": brow["fidelity"], "difference_B_minus_A": brow["fidelity"] - arow["fidelity"]},
        {"metric": "depth", "processor_A": arow["depth"], "processor_B": brow["depth"], "difference_B_minus_A": brow["depth"] - arow["depth"]},
        {"metric": "two_qubit_gates", "processor_A": arow["two_qubit_gates"], "processor_B": brow["two_qubit_gates"], "difference_B_minus_A": brow["two_qubit_gates"] - arow["two_qubit_gates"]},
        {"metric": "swap_overhead", "processor_A": arow["swap_overhead"], "processor_B": brow["swap_overhead"], "difference_B_minus_A": brow["swap_overhead"] - arow["swap_overhead"]},
        {"metric": "postselection_yield", "processor_A": arow["postselection_yield"], "processor_B": brow["postselection_yield"], "difference_B_minus_A": brow["postselection_yield"] - arow["postselection_yield"]},
    ])
    comparison.to_csv(RESULTS / "AB_comparison.csv", index=False)

    print(df.to_string(index=False))
    print("\nSaved:", RESULTS / "bell_processor_metrics.csv")
    print("Saved:", RESULTS / "AB_comparison.csv")


if __name__ == "__main__":
    main()
