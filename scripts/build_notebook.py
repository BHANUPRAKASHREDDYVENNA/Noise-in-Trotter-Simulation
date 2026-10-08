from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def cell(kind: str, text: str) -> dict:
    return {
        "cell_type": kind,
        "metadata": {},
        "source": text.splitlines(True),
        **({"execution_count": None, "outputs": []} if kind == "code" else {}),
    }


def build() -> None:
    cells = [
        cell("markdown", "# Qiskit Fall Fest 2026 — Phase 1\n## S3: Noise in Trotter Simulation\n"),
        cell("markdown", "Phase-1 workflow: one PS, same logical workload on A/B, architecture/resource metrics, evidence-based comparison and reproducibility. Numerical demonstration settings are illustrative."),
        cell("code", "import json\nfrom pathlib import Path\nconfig = json.loads((Path('data') / 'practice_config.json').read_text())\nconfig"),
        cell("markdown", "## Processor graph\nA processor is qubits plus a coupling map; nonadjacent interactions can require routing."),
        cell("code", "from src.practice_s3 import logical_trotter_circuit, PracticeProcessor, compile_practice\ns=config['system']\nlogical=logical_trotter_circuit(s['trotter_steps'],s['total_time'],s['J'],s['h'])\nmodels={}\nfor key in ['A','B']:\n    p=config['processors'][key]\n    models[key]=PracticeProcessor(p['name'],s['n_qubits'],tuple(tuple(e) for e in p['coupling_map']),p['p1'],p['p2'],p['readout_error'])\ncompiled={k:compile_practice(logical,v) for k,v in models.items()}\nprint(len(logical),len(compiled['A']),len(compiled['B']))"),
        cell("markdown", "## A/B experiment\nRun the same logical Trotter workload on the two illustrative architectures."),
        cell("code", "from src.practice_s3 import ideal_exact_state, benchmark_processor\nimport pandas as pd\nexact=ideal_exact_state(s['n_qubits'],s['total_time'],s['J'],s['h'])\nrows=[]\nfor i,key in enumerate(['A','B']):\n    row=benchmark_processor(models[key],logical,exact,s['n_qubits'],int(config['shots_or_trajectories']),int(config['seed'])+i)\n    row['processor']=key; row['processor_name']=models[key].name; rows.append(row)\ndf=pd.DataFrame(rows)\ndf"),
        cell("markdown", "## Interpretation\nCompare fidelity/quality against depth, two-qubit operations and routing overhead. Explain observations using measured evidence and document uncertainty and limitations."),
    ]
    nb = {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": "3.11"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }
    (ROOT / "main.ipynb").write_text(json.dumps(nb, indent=2), encoding="utf-8")


if __name__ == "__main__":
    build()
