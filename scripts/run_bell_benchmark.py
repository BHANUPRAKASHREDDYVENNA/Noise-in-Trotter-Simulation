from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.bell_benchmark import ProcessorModel, benchmark_bell_processor
from src.processors import validate_processor_definition

RESULTS = ROOT / "results" / "tables"


def load(path: Path) -> dict:
    definition = json.loads(path.read_text(encoding="utf-8"))
    validate_processor_definition(definition, path.name)
    return definition


def main() -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    definitions = {
        "A": load(ROOT / "processors" / "processor_A.json"),
        "B": load(ROOT / "processors" / "processor_B.json"),
    }

    models = [
        ProcessorModel(
            definitions[label]["name"],
            definitions[label]["num_qubits"],
            tuple(map(tuple, definitions[label]["coupling_map"])),
            definitions[label]["noise"]["p1"],
            definitions[label]["noise"]["p2"],
            definitions[label]["noise"]["readout_error"],
        )
        for label in ("A", "B")
    ]

    rows = [benchmark_bell_processor(model, shots=2048, seed=7) for model in models]
    df = pd.DataFrame(rows)
    df.to_csv(RESULTS / "bell_processor_metrics.csv", index=False)

    arow, brow = df.iloc[0], df.iloc[1]
    metrics = (
        "fidelity",
        "depth",
        "two_qubit_gates",
        "swap_overhead",
        "physical_qubits",
        "postselection_yield",
        "effective_noise",
        "readout_error",
    )
    comparison = pd.DataFrame(
        [
            {
                "metric": metric,
                "processor_A": float(arow[metric]),
                "processor_B": float(brow[metric]),
                "difference_B_minus_A": float(brow[metric] - arow[metric]),
            }
            for metric in metrics
        ]
    )
    comparison.to_csv(RESULTS / "AB_comparison.csv", index=False)
    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
