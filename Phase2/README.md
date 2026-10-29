# Partner Plus IBM Qiskit Fall Fest 2026 — Phase 2 PS-S3 Benchmark Suite
## Track 3: Quantum Simulation (Hamiltonian Dynamics)
### Problem Statement PS-S3: Noise Accumulation in Trotter Circuits

> **Event:** IBM Partner Plus · SRM University-AP Qiskit Fall Fest 2026 On-Campus Hackathon (Phase 2)  
> **Team Name:** `QUANTUM'S`  
> **Team Lead:** **Bhanu Prakash Venna**  
> **Affiliation:** Department of Computer Science & Engineering, SRM University-AP  
> **Public Repository:** [https://github.com/BHANUPRAKASHREDDYVENNA/Noise-in-Trotter-Simulation](https://github.com/BHANUPRAKASHREDDYVENNA/Noise-in-Trotter-Simulation)  
> **Hackathon Portal:** [https://www.qffsrmap2026.com/learning/hackathon](https://www.qffsrmap2026.com/learning/hackathon)  
> **Deadline:** Day 2 (30 October 2026) at 5:40 PM IST

---

## 🏆 Phase 2 Executive Summary & Scientific Discoveries

This directory contains the complete, self-contained, and reproducible Phase 2 implementation for **Problem Statement PS-S3: Noise Accumulation in Trotter Circuits**.

We investigate the quantum dynamics of a 4-spin one-dimensional Transverse-Field Ising Model (TFIM) on a **periodic ring** evolved to target time $T = 2.0$, quantitatively resolving the fundamental trade-off between algorithmic Trotter discretization error and physical device noise accumulation:
$$\text{Total Error}(n) \approx \underbrace{\mathcal{O}\left(\frac{T^2}{n}\right)}_{\text{Algorithmic Discretization Error}} + \underbrace{\mathcal{O}\left(n \cdot N_{\rm CX/step} \cdot p_2\right)}_{\text{Physical Gate Noise Accumulation}}$$

### Key Discoveries:
1. **The Trotter-Noise Crossover ($n^*$):**  
   Across a 12-point Trotter step grid $n \in \{1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16\}$, we identify an optimal step count **$n^* = 7$** for native 4-cycle architectures (Processors B and D) under official standard noise ($p_1=0.001, p_2=0.005, p_{\rm ro}=0.01$), achieving peak density-matrix state fidelity **$\mathcal{F}^* = 0.6628$**.
2. **Noise Scaling Dynamics on Custom Processor D:**  
   Sweeping the noise scaling factor directly validates the theoretical scaling of the crossover point:
   - **Low Noise ($0.5\times$):** Discretization error dominates longer, shifting the optimum upward to **$n^* = 8$** with peak fidelity **$\mathcal{F}^* = 0.7821$**.
   - **Standard Noise ($1.0\times$):** Balanced regime yields **$n^* = 7$** with peak fidelity **$\mathcal{F}^* = 0.6628$**.
   - **High Noise ($2.0\times$):** Physical gate errors accumulate twice as fast, suppressing deep circuits and shifting the optimum downward to **$n^* = 6$** with peak fidelity **$\mathcal{F}^* = 0.5031$**.
3. **Topological Routing Penalty on Tree Graphs (Processor A):**  
   Processor A (5-qubit tree baseline) lacks a 4-cycle. Simulating the periodic boundary condition bond $(3, 0)$ requires routing SWAP networks (**11 SWAP gates / 33 routing CX gates** at $n=6$), exploding two-qubit depth from 24 to 57 and depressing peak fidelity to **$0.5774$** (an absolute degradation of $8.54\%$ and relative loss of $12.89\%$ compared to Processor D).
4. **Custom Processor D Co-Design (Objective 2):**  
   Our 9-qubit cubic hypercube hybrid architecture embeds native 4-cycles with diameter 3, average path length 1.778, and maximum degree 4. It executes the ring TFIM with **zero routing SWAPs**, passing all official constraints verified by `check_processor_d.py`.
5. **Entanglement Verification (Objective 1):**  
   Bell-state parity measurements on Processor D yield $\mathcal{F} = 0.9633 \pm 0.0021$ on adjacent pair $(0, 1)$ ($d=1$, 1 CX) and $\mathcal{F} = 0.9476 \pm 0.0025$ on distant pair $(0, 6)$ ($d=3$, 7 CX due to 2 routing SWAPs).
6. **Error Mitigation Advantage (Bonus):**  
   Digital Zero-Noise Extrapolation (ZNE) via unitary gate folding ($\lambda \in [1, 3, 5]$) recovers the unmitigated staggered magnetization from $M_s = 0.4403$ (error $0.2121$) to $M_s^{\rm ZNE} = 0.4971$ (error $0.1553$), demonstrating a **$>26.8\%$ error reduction**.

---

## 📊 Phase 2 Benchmark Results Summary

### Table 1: Optimal Trotter Step Counts ($n^*$) & Peak Fidelity
*Source: `results/tables/s3_summary.csv` (Exact classical ground truth: $M_s^{\rm exact}(T=2.0) = 0.652444$)*

| Processor | Topology | Noise Scale | Routing SWAPs | Optimal Steps $n^*$ | Peak State Fidelity $\mathcal{F}^*$ | Ideal Trotter Fidelity | Noisy Staggered Magnetization $M_s(n^*)$ |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Processor A** | 5Q Tree Baseline | $1.0\times$ | **11** | **6** | **0.5774** | 0.9934 | $0.4131 \pm 0.0142$ |
| **Processor B** | 9Q Heavy-Hex Baseline | $1.0\times$ | **0** | **7** | **0.6628** | 0.9951 | $0.4403 \pm 0.0141$ |
| **Processor D** | 9Q Cubic Hybrid (Ours) | $1.0\times$ | **0** | **7** | **0.6628** | 0.9951 | $0.4403 \pm 0.0141$ |
| **Processor D** | 9Q Cubic Hybrid (Ours) | $0.5\times$ | **0** | **8** | **0.7821** | 0.9963 | $0.5361 \pm 0.0132$ |
| **Processor D** | 9Q Cubic Hybrid (Ours) | $2.0\times$ | **0** | **6** | **0.5031** | 0.9934 | $0.3242 \pm 0.0148$ |

### Table 2: Objective 1 Bell-State Entanglement on Processor D
*Source: `results/tables/bell.csv` ($N = 4,096$ shots per basis)*

| Physical Pair | Graph Distance | Execution Mode | $\langle XX \rangle \pm \mathrm{SE}$ | $\langle YY \rangle \pm \mathrm{SE}$ | $\langle ZZ \rangle \pm \mathrm{SE}$ | Bell State Fidelity $\mathcal{F} \pm \mathrm{SE}$ | 2Q CX Gates |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `(0, 1)` | $d=1$ (Near) | ideal | $1.0000 \pm 0.0000$ | $-1.0000 \pm 0.0000$ | $1.0000 \pm 0.0000$ | **$1.0000 \pm 0.0000$** | 1 |
| `(0, 1)` | $d=1$ (Near) | noisy | $0.9497 \pm 0.0049$ | $-0.9507 \pm 0.0048$ | $0.9531 \pm 0.0047$ | **$0.9633 \pm 0.0021$** | 1 |
| `(0, 6)` | $d=3$ (Far) | ideal | $1.0000 \pm 0.0000$ | $-1.0000 \pm 0.0000$ | $1.0000 \pm 0.0000$ | **$1.0000 \pm 0.0000$** | 7 |
| `(0, 6)` | $d=3$ (Far) | noisy | $0.9312 \pm 0.0057$ | $-0.9341 \pm 0.0056$ | $0.9258 \pm 0.0059$ | **$0.9476 \pm 0.0025$** | 7 |

### Table 3: Bonus Zero-Noise Extrapolation (ZNE) at $n^* = 7$ on Processor D
*Source: `results/tables/mitigation.csv` ($12,288$ shots total)*

| Scale Factor $\lambda$ | Folding Order $k$ | CX Gates | Measured $M_s \pm \mathrm{SE}$ | Extrapolated $M_s^{\rm ZNE}$ | Exact Ground Truth $M_s$ | Absolute Error | Relative Error Reduction |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| $\lambda = 1$ (Raw) | 0 | 56 | $0.4403 \pm 0.0141$ | — | $0.652444$ | $0.2121$ | Baseline |
| $\lambda = 3$ | 1 | 168 | $0.3276 \pm 0.0148$ | — | $0.652444$ | $0.3248$ | — |
| $\lambda = 5$ | 2 | 280 | $0.2114 \pm 0.0152$ | — | $0.652444$ | $0.4410$ | — |
| **$\lambda \to 0$ (Mitigated)** | — | — | — | **$0.4971$** | **$0.652444$** | **$0.1553$** | **$> 26.8\%$ Reduction** |

---

## 🛠️ Directory Contents & Structure

```
Phase2/
├── README.md                          # Phase 2 documentation & benchmark summary
├── report.md                          # Phase 2 scientific report (publication format)
├── main.ipynb                         # Pre-executed Phase 2 master notebook with rich outputs
├── qff_sim.py                         # Authoritative organizer simulation module
├── check_processor_d.py               # Official Phase 2 validator (root entry point)
├── processors/
│   ├── processor_A.json               # 5-qubit tree baseline
│   ├── processor_B.json               # 9-qubit heavy-hex baseline
│   └── processor_D.json               # 9-qubit cubic hypercube hybrid (checker-verified)
├── tools/
│   └── check_processor_d.py           # Official Phase 2 validator tool
├── data/
│   ├── instances_index.json           # Challenge instance manifest
│   └── s3/
│       └── tfim_ring_N4_g1.00.json    # Locked 4-spin ring TFIM Hamiltonian
├── scripts/
│   ├── run_phase2_s3.py               # Complete Phase 2 benchmark pipeline
│   ├── make_phase2_figures.py         # Publication-grade figure generator
│   ├── build_phase2_notebook.py       # Deterministic notebook builder
│   └── validate_submission.py         # Automated contract validator
├── results/
│   ├── tables/
│   │   ├── bell.csv                   # Objective 1 Bell states
│   │   ├── s3_scan.csv                # 60-row step scan (n in 1..16)
│   │   ├── s3_summary.csv             # Crossover summary (n*, peak F)
│   │   ├── resources.csv              # Gate count & routing decomposition
│   │   └── mitigation.csv             # Zero-noise extrapolation
│   └── figures/
│       ├── s3_fidelity_crossover.png  # Fidelity crossover & staggered magnetization
│       ├── s3_noise_sweep_D.png       # 0.5x, 1.0x, 2.0x noise scaling shifts
│       ├── s3_gate_split.png          # Logical vs SWAP routing CX gate split
│       ├── bell_correlations_D.png    # Parity bars & tomography fidelity
│       ├── s3_zne_mitigation.png      # Richardson ZNE linear extrapolation
│       └── processor_topologies.png   # Graph comparison (A, B, D)
└── tests/
    ├── test_phase2_s3.py              # Phase 2 unit & regression tests
    └── test_*.py                      # Full test suite (58 tests passing)
```

---

## 🚀 Quickstart: Running Phase 2

All Phase 2 execution commands run directly from within `Phase2/`:

```bash
cd Phase2

# 1. Validate custom Processor D
python check_processor_d.py processors/processor_D.json 4

# 2. Run the complete Phase 2 benchmark campaign (~2 minutes)
python scripts/run_phase2_s3.py

# 3. Render all publication figures
python scripts/make_phase2_figures.py

# 4. Run the Phase 2 test suite
python -m pytest -q

# 5. Execute master notebook
jupyter nbconvert --to notebook --execute main.ipynb
```
