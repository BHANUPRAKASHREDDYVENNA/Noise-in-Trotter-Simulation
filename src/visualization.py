from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def ensure_dirs():
    Path("results/tables").mkdir(parents=True, exist_ok=True)
    Path("results/figures").mkdir(parents=True, exist_ok=True)


def plot_ab_bar(df: pd.DataFrame, metric: str, output: str):
    required = {"processor", metric}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns for plot: {sorted(missing)}")
    ax = df.plot.bar(x="processor", y=metric, legend=False)
    ax.set_title(f"Processor A vs B — {metric}")
    ax.set_ylabel(metric)
    plt.tight_layout()
    plt.savefig(output, dpi=180)
    plt.close()
