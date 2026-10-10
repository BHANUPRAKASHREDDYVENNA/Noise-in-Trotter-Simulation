from __future__ import annotations

import json
from pathlib import Path
import sys

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.practice_s3 import (
    PracticeProcessor,
    benchmark_processor,
    ideal_exact_state,
    logical_trotter_circuit,
)
from src.validation import validate_trotter_parameters


def main() -> None:
    cfg = json.loads((ROOT / "data" / "practice_config.json").read_text(encoding="utf-8"))
    system = cfg["system"]
    trajectories = int(cfg["shots_or_trajectories"])

    validate_trotter_parameters(
        n_qubits=int(system["n_qubits"]),
        steps=int(system["trotter_steps"]),
        total_time=float(system["total_time"]),
        coupling=float(system["J"]),
        field=float(system["h"]),
        trajectories=trajectories,
    )

    logical = logical_trotter_circuit(
        int(system["trotter_steps"]),
        float(system["total_time"]),
        float(system["J"]),
        float(system["h"]),
        n_qubits=int(system["n_qubits"]),
    )
    exact = ideal_exact_state(
        int(system["n_qubits"]),
        float(system["total_time"]),
        float(system["J"]),
        float(system["h"]),
    )

    processors = {}
    for key in ("A", "B"):
        config = cfg["processors"][key]
        processors[key] = PracticeProcessor(
            name=config["name"],
            num_qubits=int(system["n_qubits"]),
            coupling_map=tuple(tuple(edge) for edge in config["coupling_map"]),
            p1=float(config["p1"]),
            p2=float(config["p2"]),
            readout_error=float(config["readout_error"]),
        )

    rows = []
    for index, key in enumerate(("A", "B")):
        result = benchmark_processor(
            processors[key],
            logical,
            exact,
            int(system["n_qubits"]),
            trajectories,
            int(cfg["seed"]) + index,
        )
        result["processor"] = key
        result["processor_name"] = processors[key].name
        rows.append(result)

    df = pd.DataFrame(rows).sort_values("processor").reset_index(drop=True)
    if list(df["processor"]) != ["A", "B"]:
        raise RuntimeError("Practice benchmark must produce exactly Processor A and Processor B.")

    output = ROOT / "results" / "tables"
    output.mkdir(parents=True, exist_ok=True)
    df.to_csv(output / "practice_ab_comparison.csv", index=False)

    for _, row in df.iterrows():
        key = row["processor"]
        pd.DataFrame([row]).to_csv(
            output / f"practice_processor_{key}_metrics.csv",
            index=False,
        )

    print(df.to_string(index=False))


if __name__ == "__main__":
    main()
