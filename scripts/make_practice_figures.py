from __future__ import annotations

import json
from math import cos, pi, sin
from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "results" / "tables" / "practice_ab_comparison.csv"
FIG = ROOT / "results" / "figures"
CONFIG = ROOT / "data" / "practice_config.json"


def save_bar(
    df: pd.DataFrame,
    columns: list[str],
    title: str,
    ylabel: str,
    filename: str,
) -> None:
    missing = set(columns) - set(df.columns)
    if missing:
        raise ValueError(f"Missing figure columns: {sorted(missing)}")
    fig, ax = plt.subplots(figsize=(8, 4.5))
    df.set_index("processor")[columns].plot.bar(ax=ax)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    fig.tight_layout()
    fig.savefig(FIG / filename, dpi=180, bbox_inches="tight")
    plt.close(fig)


def processor_definition(label: str) -> dict:
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    path = ROOT / cfg["processor_files"][label]
    return json.loads(path.read_text(encoding="utf-8"))


def save_processor_graph(label: str) -> None:
    definition = processor_definition(label)
    edges = [tuple(edge) for edge in definition["coupling_map"]]
    n = int(definition["num_qubits"])

    if n == 1:
        positions = {0: (0.0, 0.0)}
    else:
        positions = {
            node: (
                cos(2 * pi * node / n),
                sin(2 * pi * node / n),
            )
            for node in range(n)
        }

    fig, ax = plt.subplots(figsize=(7, 4.5))
    for a, b in edges:
        ax.plot(
            [positions[a][0], positions[b][0]],
            [positions[a][1], positions[b][1]],
            linewidth=2.5,
            marker=None,
        )

    for node, (x, y) in positions.items():
        ax.scatter([x], [y], s=900)
        ax.text(x, y, str(node), ha="center", va="center", color="white", fontsize=12)

    ax.set_title(
        f"Processor {label} — {n}Q {definition['architecture']}"
    )
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(
        FIG / f"processor_{label}_graph.svg",
        format="svg",
        bbox_inches="tight",
    )
    plt.close(fig)


def main() -> None:
    if not TABLE.is_file():
        raise FileNotFoundError(f"Practice result table not found: {TABLE}")
    df = pd.read_csv(TABLE)
    if set(df["processor"]) != {"A", "B"}:
        raise ValueError("Practice result table must contain Processor A and B.")

    FIG.mkdir(parents=True, exist_ok=True)
    save_bar(
        df,
        ["mean_fidelity", "measured_z0_expectation"],
        "Source-document A/B performance",
        "Metric",
        "AB_performance.svg",
    )
    save_bar(
        df,
        ["depth", "two_qubit_gate_count", "swap_count"],
        "Source-document A/B architecture trade-offs",
        "Count / depth",
        "architecture_tradeoffs.svg",
    )
    save_processor_graph("A")
    save_processor_graph("B")


if __name__ == "__main__":
    main()
