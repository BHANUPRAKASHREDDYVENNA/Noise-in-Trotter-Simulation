from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def ensure_dirs(root: str | Path = ".") -> tuple[Path, Path]:
    root = Path(root)
    tables = root / "results" / "tables"
    figures = root / "results" / "figures"
    tables.mkdir(parents=True, exist_ok=True)
    figures.mkdir(parents=True, exist_ok=True)
    return tables, figures


def plot_ab_bar(df: pd.DataFrame, metric: str, output: str | Path) -> Path:
    if not isinstance(df, pd.DataFrame):
        raise TypeError("df must be a pandas DataFrame.")
    if df.empty:
        raise ValueError("Cannot plot an empty data frame.")
    required = {"processor", metric}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns for plot: {sorted(missing)}")
    values = pd.to_numeric(df[metric], errors="coerce")
    if values.isna().any():
        raise ValueError(f"Metric {metric} contains non-numeric values.")

    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.bar(df["processor"].astype(str), values)
    ax.set_title(f"Processor A vs B — {metric}")
    ax.set_ylabel(metric)
    fig.tight_layout()
    fig.savefig(output, dpi=180, bbox_inches="tight")
    plt.close(fig)
    return output
