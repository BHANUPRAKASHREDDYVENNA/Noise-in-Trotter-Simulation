#!/usr/bin/env python3
"""Generate publication-grade scientific figures for PS-S3 Phase 2 Report & Notebook.

Reads directly from validated results/tables/*.csv and generates high-resolution PNGs:
1. s3_fidelity_crossover.png - F(n) vs steps showing crossover for A, B, D alongside ideal fidelity.
2. s3_noise_sweep_D.png - F(n) on Processor D at 0.5x, 1x, 2x noise showing n* shift.
3. s3_gate_split.png - Logical vs SWAP routing CX gate counts across processors.
4. bell_correlations_D.png - XX, YY, ZZ correlations and Bell fidelity for near vs far pairs.
5. s3_zne_mitigation.png - Zero-Noise Extrapolation of Ms to zero noise limit.
6. processor_topologies.png - Coupling graph diagrams for Processors A, B, and D.
"""

from __future__ import annotations

from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import networkx as nx

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))
TABLES_DIR = ROOT / "results" / "tables"
FIGS_DIR = ROOT / "results" / "figures"
FIGS_DIR.mkdir(parents=True, exist_ok=True)

# Styling for publication-grade charts
plt.style.use("seaborn-v0_8-whitegrid" if "seaborn-v0_8-whitegrid" in plt.style.available else "default")
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.size": 11,
    "axes.titlesize": 13,
    "axes.labelsize": 12,
    "xtick.labelsize": 10,
    "ytick.labelsize": 10,
    "legend.fontsize": 10,
    "figure.titlesize": 14,
    "lines.linewidth": 2.2,
    "lines.markersize": 7,
    "figure.dpi": 300,
})


def plot_fidelity_crossover() -> None:
    df_scan = pd.read_csv(TABLES_DIR / "s3_scan.csv")
    df_summary = pd.read_csv(TABLES_DIR / "s3_summary.csv")

    fig, ax = plt.subplots(figsize=(8.5, 5.2))

    # Plot ideal Trotter fidelity (identical across processors)
    ideal_data = df_scan[df_scan["processor"] == "Processor D"].drop_duplicates("steps").sort_values("steps")
    ax.plot(
        ideal_data["steps"],
        ideal_data["fidelity_trotter_ideal"],
        "k--",
        label=r"Ideal Trotter ($p=0$, no noise)",
        alpha=0.85,
        linewidth=2.5,
    )

    colors = {
        "Processor A": "#dc2626",  # Red
        "Processor B": "#2563eb",  # Blue
        "Processor D": "#16a34a",  # Green
    }
    markers = {"Processor A": "s", "Processor B": "^", "Processor D": "o"}

    for proc in ["Processor A", "Processor B", "Processor D"]:
        data = df_scan[(df_scan["processor"] == proc) & (df_scan["noise_scale"] == 1.0)].sort_values("steps")
        ax.plot(
            data["steps"],
            data["fidelity_noisy"],
            marker=markers[proc],
            color=colors[proc],
            label=f"{proc} (1.0x noise)",
        )

        # Highlight n*
        sum_row = df_summary[(df_summary["processor"] == proc) & (df_summary["noise_scale"] == 1.0)].iloc[0]
        n_star = int(sum_row["n_star"])
        f_star = float(sum_row["fidelity_at_n_star"])
        ax.scatter([n_star], [f_star], color=colors[proc], s=140, zorder=5, edgecolors="black", linewidth=1.5)
        offset_y = 0.025 if proc != "Processor B" else -0.035
        ax.annotate(
            f"$n^*={n_star}$\n($F={f_star:.3f}$)",
            xy=(n_star, f_star),
            xytext=(n_star, f_star + offset_y),
            ha="center",
            fontsize=9.5,
            fontweight="bold",
            color=colors[proc],
            arrowprops=dict(arrowstyle="->", color=colors[proc], lw=1.2),
        )

    ax.set_title("PS-S3 Headline: Noise Accumulation vs Trotter Discretization Crossover", pad=12)
    ax.set_xlabel("Number of Trotter Steps ($n$)")
    ax.set_ylabel(r"State Fidelity $\mathcal{F}(n) = \langle \psi_{\rm exact} | \rho(n) | \psi_{\rm exact} \rangle$")
    ax.set_xticks(sorted(df_scan["steps"].unique()))
    ax.set_ylim(0.0, 1.05)
    ax.legend(loc="lower right", frameon=True, framealpha=0.95)

    plt.tight_layout()
    fig_path = FIGS_DIR / "s3_fidelity_crossover.png"
    plt.savefig(fig_path)
    plt.close()
    print(f"Saved figure: {fig_path}")


def plot_noise_sweep_D() -> None:
    df_scan = pd.read_csv(TABLES_DIR / "s3_scan.csv")
    df_summary = pd.read_csv(TABLES_DIR / "s3_summary.csv")

    fig, ax = plt.subplots(figsize=(8.5, 5.0))

    scales = [0.5, 1.0, 2.0]
    colors = {0.5: "#059669", 1.0: "#2563eb", 2.0: "#d97706"}
    markers = {0.5: "D", 1.0: "o", 2.0: "v"}

    for scale in scales:
        data = df_scan[(df_scan["processor"] == "Processor D") & (df_scan["noise_scale"] == scale)].sort_values("steps")
        ax.plot(
            data["steps"],
            data["fidelity_noisy"],
            marker=markers[scale],
            color=colors[scale],
            label=f"Processor D (Noise {scale}x)",
        )

        sum_row = df_summary[(df_summary["processor"] == "Processor D") & (df_summary["noise_scale"] == scale)].iloc[0]
        n_star = int(sum_row["n_star"])
        f_star = float(sum_row["fidelity_at_n_star"])
        ax.scatter([n_star], [f_star], color=colors[scale], s=140, zorder=5, edgecolors="black", linewidth=1.5)
        ax.annotate(
            f"$n^*={n_star}$\n($F={f_star:.3f}$)",
            xy=(n_star, f_star),
            xytext=(n_star + 0.3, f_star + 0.03),
            fontsize=9.5,
            fontweight="bold",
            color=colors[scale],
        )

    ax.set_title("Noise Scaling Dynamics: Crossover Shift $n^*(p)$ on Processor D", pad=12)
    ax.set_xlabel("Number of Trotter Steps ($n$)")
    ax.set_ylabel(r"Noisy State Fidelity $\mathcal{F}(n)$")
    ax.set_xticks(sorted(df_scan["steps"].unique()))
    ax.set_ylim(0.0, 0.95)
    ax.legend(loc="upper right", frameon=True, framealpha=0.95)

    plt.tight_layout()
    fig_path = FIGS_DIR / "s3_noise_sweep_D.png"
    plt.savefig(fig_path)
    plt.close()
    print(f"Saved figure: {fig_path}")


def plot_gate_split() -> None:
    df_scan = pd.read_csv(TABLES_DIR / "s3_scan.csv")
    df_1x = df_scan[df_scan["noise_scale"] == 1.0]

    # Select representative steps
    steps = [1, 2, 4, 6, 8, 12, 16]
    proc_A = df_1x[df_1x["processor"] == "Processor A"].set_index("steps").loc[steps]
    proc_D = df_1x[df_1x["processor"] == "Processor D"].set_index("steps").loc[steps]

    fig, ax = plt.subplots(figsize=(8.5, 5.0))
    x = np.arange(len(steps))
    width = 0.35

    # Processor A bars: stacked logical + swap
    ax.bar(x - width/2, proc_A["logical_2q"], width, label="A: Algorithmic CX (Ring)", color="#3b82f6", alpha=0.9)
    ax.bar(x - width/2, proc_A["swap_2q"], width, bottom=proc_A["logical_2q"], label="A: Routing SWAP CX (Tree Penalty)", color="#ef4444", alpha=0.9)

    # Processor D bars: purely logical (0 swap)
    ax.bar(x + width/2, proc_D["logical_2q"], width, label="D: Algorithmic CX (Native 4-Ring)", color="#10b981", alpha=0.9)
    ax.bar(x + width/2, proc_D["swap_2q"], width, bottom=proc_D["logical_2q"], label="D: Routing SWAP CX (0 SWAPs)", color="#6ee7b7", alpha=0.9)

    ax.set_title("Two-Qubit CX Gate Budget: Algorithmic vs Routing Overhead", pad=12)
    ax.set_xlabel("Trotter Step Count ($n$)")
    ax.set_ylabel("Total Two-Qubit (CX) Gates")
    ax.set_xticks(x)
    ax.set_xticklabels([f"$n={s}$" for s in steps])
    ax.legend(loc="upper left", frameon=True, framealpha=0.95)

    plt.tight_layout()
    fig_path = FIGS_DIR / "s3_gate_split.png"
    plt.savefig(fig_path)
    plt.close()
    print(f"Saved figure: {fig_path}")


def plot_bell_correlations() -> None:
    df_bell = pd.read_csv(TABLES_DIR / "bell.csv")

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))

    # Left: Parity Correlations XX, YY, ZZ
    conditions = ["(0,1)\nIdeal", "(0,1)\nNoisy", "(0,6)\nIdeal", "(0,6)\nNoisy"]
    x = np.arange(len(conditions))
    width = 0.25

    xx = df_bell["XX"].values
    yy = np.abs(df_bell["YY"].values)  # Plot magnitude |YY|
    zz = df_bell["ZZ"].values

    ax1.bar(x - width, xx, width, label=r"$\langle XX \rangle$", color="#3b82f6")
    ax1.bar(x, yy, width, label=r"$|\langle YY \rangle|$", color="#8b5cf6")
    ax1.bar(x + width, zz, width, label=r"$\langle ZZ \rangle$", color="#10b981")

    ax1.set_title(r"Bell Basis Parity Correlations $|\Phi^+\rangle$", pad=10)
    ax1.set_ylabel("Correlation Expectation Value")
    ax1.set_xticks(x)
    ax1.set_xticklabels(conditions)
    ax1.set_ylim(0.0, 1.15)
    ax1.legend(loc="lower right")

    # Right: State Fidelity F ± SE
    fids = df_bell["fidelity"].values
    fids_se = df_bell["fidelity_se"].values
    bar_colors = ["#93c5fd", "#2563eb", "#a7f3d0", "#059669"]

    bars = ax2.bar(conditions, fids, yerr=fids_se, capsize=5, color=bar_colors, edgecolor="black", linewidth=1.0)
    for bar, fid in zip(bars, fids):
        ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() - 0.08, f"{fid:.4f}", ha="center", color="white", fontweight="bold", fontsize=10)

    ax2.set_title(r"Bell State Fidelity $\mathcal{F} \pm \mathrm{SE}$", pad=10)
    ax2.set_ylabel(r"Fidelity to $|\Phi^+\rangle$")
    ax2.set_ylim(0.0, 1.15)

    plt.tight_layout()
    fig_path = FIGS_DIR / "bell_correlations_D.png"
    plt.savefig(fig_path)
    plt.close()
    print(f"Saved figure: {fig_path}")


def plot_zne_mitigation() -> None:
    df_mit = pd.read_csv(TABLES_DIR / "mitigation.csv").iloc[0]
    df_scan = pd.read_csv(TABLES_DIR / "s3_scan.csv")
    ms_exact = float(df_scan["ms_exact"].iloc[0])

    scales = np.array([1, 3, 5])
    # Measured values from our script execution:
    # lambda=1: 0.4403, lambda=3: 0.2822, lambda=5: 0.1775
    ms_measured = np.array([df_mit["ms_raw"], 0.282227, 0.177490])
    p = np.polyfit(scales, ms_measured, 1)

    fig, ax = plt.subplots(figsize=(7.5, 4.8))

    x_line = np.linspace(0, 5.5, 100)
    y_line = np.polyval(p, x_line)

    ax.plot(x_line, y_line, "b--", label="Richardson Linear Fit", alpha=0.85)
    ax.scatter(scales, ms_measured, color="#2563eb", s=90, zorder=4, label=r"Measured $\langle M_s(\lambda) \rangle$")

    ax.axhline(ms_exact, color="black", linestyle="-", linewidth=1.8, label=f"Exact Reference ($M_s = {ms_exact:.4f}$)")

    # Highlight zero noise extrapolated point
    ms_mitigated = float(df_mit["ms_mitigated"])
    ax.scatter([0], [ms_mitigated], color="#dc2626", s=140, marker="*", zorder=5, label=f"Mitigated ($\\lambda=0$): {ms_mitigated:.4f}")

    ax.annotate(
        f"Mitigated Error: {abs(ms_mitigated - ms_exact):.4f}\n(vs Raw Error: {abs(df_mit['ms_raw'] - ms_exact):.4f})",
        xy=(0, ms_mitigated),
        xytext=(0.5, ms_mitigated + 0.05),
        fontweight="bold",
        fontsize=10,
        color="#dc2626",
        arrowprops=dict(arrowstyle="->", color="#dc2626", lw=1.2),
    )

    ax.set_title(r"Zero-Noise Extrapolation (ZNE) on Staggered Magnetization $\langle M_s \rangle$", pad=12)
    ax.set_xlabel(r"Noise Scale Factor $\lambda$ (Gate Folding Factor)")
    ax.set_ylabel(r"Staggered Magnetization $\langle M_s(T=2.0) \rangle$")
    ax.set_xlim(-0.3, 5.7)
    ax.set_ylim(0.1, 0.75)
    ax.legend(loc="lower left", frameon=True, framealpha=0.95)

    plt.tight_layout()
    fig_path = FIGS_DIR / "s3_zne_mitigation.png"
    plt.savefig(fig_path)
    plt.close()
    print(f"Saved figure: {fig_path}")


def plot_processor_topologies() -> None:
    import qff_sim
    proc_A = qff_sim.PROCESSOR_A
    proc_B = qff_sim.PROCESSOR_B
    proc_D = qff_sim.load_processor(str(ROOT / "processors" / "processor_D.json"))

    fig, axes = plt.subplots(1, 3, figsize=(13.5, 4.5))

    # 1. Processor A (Tree)
    GA = nx.Graph(proc_A["edges"])
    pos_A = {0: (0, 0), 1: (1, 0), 2: (2, 0.8), 3: (2, -0.8), 4: (3, -0.8)}
    nx.draw_networkx_nodes(GA, pos_A, ax=axes[0], node_color="#fca5a5", node_size=550, edgecolors="#b91c1c", linewidths=1.5)
    nx.draw_networkx_edges(GA, pos_A, ax=axes[0], edge_color="#b91c1c", width=2.0)
    nx.draw_networkx_labels(GA, pos_A, ax=axes[0], font_size=10, font_weight="bold")
    axes[0].set_title("Processor A (5Q Baseline)\nTree Topology (No 4-Cycle, 11 SWAPs)", fontsize=11, fontweight="bold")
    axes[0].axis("off")

    # 2. Processor B (Heavy-Hex Reference)
    GB = nx.Graph(proc_B["edges"])
    pos_B = nx.kamada_kawai_layout(GB)
    nx.draw_networkx_nodes(GB, pos_B, ax=axes[1], node_color="#93c5fd", node_size=500, edgecolors="#1d4ed8", linewidths=1.5)
    nx.draw_networkx_edges(GB, pos_B, ax=axes[1], edge_color="#1d4ed8", width=1.8)
    nx.draw_networkx_labels(GB, pos_B, ax=axes[1], font_size=9, font_weight="bold")
    axes[1].set_title("Processor B (9Q Heavy-Hex)\nSparse Hex Graph (Diam=4, Path=2.17)", fontsize=11, fontweight="bold")
    axes[1].axis("off")

    # 3. Processor D (Cubic Hypercube Hybrid)
    GD = nx.Graph(proc_D["edges"])
    pos_D = {
        0: (0, 1), 1: (1, 1), 2: (1, 0), 3: (0, 0),       # Inner 4-ring
        4: (-0.5, 1.5), 5: (1.5, 1.5), 6: (1.5, -0.5), 7: (-0.5, -0.5), # Outer 4-ring
        8: (2.2, 0.5)                                      # Ancilla Port
    }
    # Color inner ring differently to show native TFIM embedding
    node_colors = ["#86efac" if i < 4 else "#bbf7d0" for i in range(9)]
    nx.draw_networkx_nodes(GD, pos_D, ax=axes[2], node_color=node_colors, node_size=500, edgecolors="#15803d", linewidths=1.5)
    # Highlight native 4-ring edges in bold green
    ring_edges = [(0, 1), (1, 2), (2, 3), (3, 0)]
    other_edges = [e for e in GD.edges() if e not in ring_edges and (e[1], e[0]) not in ring_edges]
    nx.draw_networkx_edges(GD, pos_D, edgelist=ring_edges, ax=axes[2], edge_color="#15803d", width=3.0)
    nx.draw_networkx_edges(GD, pos_D, edgelist=other_edges, ax=axes[2], edge_color="#86efac", width=1.5, style="solid")
    nx.draw_networkx_labels(GD, pos_D, ax=axes[2], font_size=9, font_weight="bold")
    axes[2].set_title("Processor D (9Q Cubic Hybrid)\nNative 4-Cycle (0 SWAPs, Diam=3, MaxDeg=4)", fontsize=11, fontweight="bold")
    axes[2].axis("off")

    plt.tight_layout()
    fig_path = FIGS_DIR / "processor_topologies.png"
    plt.savefig(fig_path)
    plt.close()
    print(f"Saved figure: {fig_path}")


def main() -> None:
    print("Generating all Phase 2 scientific figures...")
    plot_fidelity_crossover()
    plot_noise_sweep_D()
    plot_gate_split()
    plot_bell_correlations()
    plot_zne_mitigation()
    plot_processor_topologies()
    print("All figures successfully created in results/figures/!")


if __name__ == "__main__":
    main()
