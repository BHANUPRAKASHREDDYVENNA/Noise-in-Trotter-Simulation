from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
TABLE = ROOT / "results" / "tables" / "practice_ab_comparison.csv"
FIG = ROOT / "results" / "figures"


def save_bar(df: pd.DataFrame, columns: list[str], title: str, ylabel: str, filename: str) -> None:
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


def main() -> None:
    if not TABLE.is_file():
        raise FileNotFoundError(f"Practice result table not found: {TABLE}")
    df = pd.read_csv(TABLE)
    if set(df["processor"]) != {"A", "B"}:
        raise ValueError("Practice result table must contain Processor A and B.")
    FIG.mkdir(parents=True, exist_ok=True)
    save_bar(df, ["mean_fidelity", "measured_z0_expectation"], "Practice-only A/B performance", "Metric", "practice_ab_performance.png")
    save_bar(df, ["depth", "two_qubit_gate_count", "swap_count"], "Practice-only architecture trade-offs", "Count / depth", "practice_architecture_tradeoffs.png")


if __name__ == "__main__":
    main()
