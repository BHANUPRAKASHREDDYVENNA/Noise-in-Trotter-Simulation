# Partner Plus IBM Qiskit Fall Fest 2026 — Track 3: Quantum Simulation
## PS-S3: Noise Accumulation in Trotter Circuits

> **Event:** IBM Partner Plus · SRM University-AP Qiskit Fall Fest 2026 Hackathon  
> **Team Name:** `QUANTUM'S`  
> **Team Lead:** **Bhanu Prakash Venna**  
> **Affiliation:** Department of Computer Science & Engineering, SRM University-AP  
> **Public Repository:** [https://github.com/BHANUPRAKASHREDDYVENNA/Noise-in-Trotter-Simulation](https://github.com/BHANUPRAKASHREDDYVENNA/Noise-in-Trotter-Simulation)  
> **Hackathon Portal:** [https://www.qffsrmap2026.com/learning/hackathon](https://www.qffsrmap2026.com/learning/hackathon)

---

## 📁 Repository Organization

This repository is organized into two clearly separated development environments:

- **`Phase1/`** — **Archived Historical Milestone:** Contains all preserved Phase 1 source files, notebooks, reports, datasets, configurations, scripts, figures, and unit tests (52 tests passing). Everything submitted for Phase 1 is preserved intact and independently executable.
- **`Phase2/`** — **Active Phase 2 Development & Competition Deliverables:** Contains all Phase 2 quantum simulation models, custom Processor D co-design, official `qff_sim.py`, benchmark pipelines, master notebook (`main.ipynb`), scientific publication report (`report.md`), high-resolution figures, CSV tables, and regression test suite (58 tests passing).
- **Repository Root (`/`)** — Houses essential shared infrastructure including `.github/workflows/`, `pyproject.toml`, `.gitignore`, `requirements.txt`, `LICENSE`, and this master documentation.

```text
Noise-in-Trotter-Simulation/
│
├── Phase1/                                    # Preserved Phase 1 historical milestone
│   ├── main.ipynb                             # Original Phase 1 master notebook (23 sections)
│   ├── report.md                              # Phase 1 architectural analysis report
│   ├── README.md                              # Phase 1 documentation
│   ├── processors/                            # Processors A, B, B_9q, D
│   ├── data/                                  # Practice configurations & guide settings
│   ├── docs/                                  # Phase 1 scope & source contract documents
│   ├── results/                               # Phase 1 SVG figures & CSV tables
│   ├── scripts/                               # Phase 1 benchmark scripts
│   ├── src/                                   # Phase 1 source code modules
│   └── tests/                                 # Phase 1 unit tests (52 tests passing)
│
├── Phase2/                                    # Active Phase 2 development & deliverables
│   ├── main.ipynb                             # Pre-executed Phase 2 master notebook (0 errors)
│   ├── report.md                              # Full Phase 2 scientific publication report
│   ├── README.md                              # Phase 2 documentation & result summary
│   ├── qff_sim.py                             # Official Phase 2 simulation module
│   ├── check_processor_d.py                   # Official Phase 2 validator (entry point)
│   ├── processors/                            # Processors A, B, D (9Q cubic hybrid)
│   ├── data/                                  # Locked 4-spin ring TFIM Hamiltonian & manifest
│   ├── scripts/                               # Phase 2 benchmark pipeline & figure scripts
│   ├── src/                                   # Phase 2 source code modules
│   ├── tests/                                 # Phase 2 unit & regression tests (58 tests passing)
│   ├── results/                               # Phase 2 publication figures & CSV tables
│   │   ├── tables/                            # bell.csv, s3_scan.csv, s3_summary.csv, etc.
│   │   └── figures/                           # High-res publication PNG plots
│   └── phase2_kit/                            # Official problem statement kit
│
├── .github/workflows/                         # Shared CI/CD workflows
├── pyproject.toml                             # Shared package & test configuration
├── requirements.txt                           # Pinned dependencies
├── LICENSE                                    # Project license
├── SECURITY.md                                # Security policy
├── .gitignore                                 # Git exclusion rules
└── README.md                                  # Repository overview (this file)
```

---

## 🏆 Phase 2 Benchmark Results Summary

*Complete details, theoretical derivations, and figures are available in [`Phase2/report.md`](Phase2/report.md) and [`Phase2/main.ipynb`](Phase2/main.ipynb).*

### Optimal Trotter Step Counts ($n^*$) & Peak Fidelity
*Physical system: 4-spin 1D periodic ring TFIM ($J=1.0, g=1.0$), initial state $|1010\rangle$, evolution time $T=2.0$.*  
*Exact classical reference: $M_s^{\rm exact}(T=2.0) = 0.652444$.*

| Processor | Topology | Noise Scale | Routing SWAPs | Optimal Steps $n^*$ | Peak State Fidelity $\mathcal{F}^*$ | Ideal Trotter Fidelity | Noisy Magnetization $M_s(n^*)$ |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **Processor A** | 5Q Tree Baseline | $1.0\times$ | **11** | **6** | **0.5774** | 0.9934 | $0.4131 \pm 0.0142$ |
| **Processor B** | 9Q Heavy-Hex Baseline | $1.0\times$ | **0** | **7** | **0.6628** | 0.9951 | $0.4403 \pm 0.0141$ |
| **Processor D** | 9Q Cubic Hybrid (Ours) | $1.0\times$ | **0** | **7** | **0.6628** | 0.9951 | $0.4403 \pm 0.0141$ |
| **Processor D** | 9Q Cubic Hybrid (Ours) | $0.5\times$ | **0** | **8** | **0.7821** | 0.9963 | $0.5361 \pm 0.0132$ |
| **Processor D** | 9Q Cubic Hybrid (Ours) | $2.0\times$ | **0** | **6** | **0.5031** | 0.9934 | $0.3242 \pm 0.0148$ |

### Objective 1 Bell-State Entanglement on Processor D
- **Near Pair `(0, 1)` ($d=1$, 1 CX):** $\mathcal{F} = 0.9633 \pm 0.0021$
- **Far Pair `(0, 6)` ($d=3$, 7 CX due to 2 routing SWAPs):** $\mathcal{F} = 0.9476 \pm 0.0025$

### Bonus Zero-Noise Extrapolation (ZNE) on Processor D
- **Unmitigated Error:** $0.2121$ ($M_s = 0.4403$)
- **Mitigated Error:** **$0.1553$** ($M_s = 0.4971$) — **$>26.8\%$ relative error reduction**

---

## 🚀 Execution & Reproducibility Guide

### 1. Global Setup
```bash
git clone https://github.com/BHANUPRAKASHREDDYVENNA/Noise-in-Trotter-Simulation.git
cd Noise-in-Trotter-Simulation
pip install -r requirements.txt
```

### 2. Running Phase 2 (Active Competition Suite)
```bash
cd Phase2

# Validate custom Processor D
python check_processor_d.py processors/processor_D.json 4

# Run complete benchmark campaign (~2 minutes)
python scripts/run_phase2_s3.py

# Render publication figures
python scripts/make_phase2_figures.py

# Run Phase 2 unit & regression tests
python -m pytest -q

# Execute Phase 2 master notebook
jupyter nbconvert --to notebook --execute main.ipynb
```

### 3. Running Phase 1 (Preserved Historical Archive)
```bash
cd Phase1

# Run Phase 1 submission validation
python scripts/validate_submission.py --practice

# Run Phase 1 tests
python -m pytest -q

# Execute Phase 1 notebook
jupyter nbconvert --to notebook --execute main.ipynb
```

### 4. Official SRM University-AP QFF 2026 Environment Reproduction
*Fully compliant with `QFF_2026_Setup_Guide_Windows.pdf` and `C:\QFF\QFF2026_TEST_REPORT.txt` (see [`Phase2/docs/qff_2026_environment_specification.md`](Phase2/docs/qff_2026_environment_specification.md)):*

```powershell
# Run the combined 110-test master suite in official hackathon venv:
cd Noise-in-Trotter-Simulation
C:\QFF\.qff2026-venv\Scripts\python.exe -m pytest -q

# Validate Processor D with official venv:
cd Phase2
C:\QFF\.qff2026-venv\Scripts\python.exe check_processor_d.py processors/processor_D.json 4

# Launch JupyterLab using official hackathon setup:
C:\QFF\.qff2026-venv\Scripts\jupyter-lab.exe
# Open Phase2/main.ipynb and select registered kernel: 'Python (QFF 2026)'
```

---

## 👥 Team & Attribution

- **Team Name:** `QUANTUM'S`
- **Team Lead:** **Bhanu Prakash Venna**  
- **Track:** Track 3 — Quantum Simulation (Hamiltonian Dynamics)  
- **Problem Statement:** PS-S3: Noise Accumulation in Trotter Circuits  
- **Department:** Department of Computer Science & Engineering, SRM University-AP  
- **Mentorship:** IBM Partner Plus & SRM University-AP Hackathon Technical Committee
