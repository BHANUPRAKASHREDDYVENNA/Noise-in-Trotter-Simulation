# Qiskit Fall Fest 2026 — Phase 1
## S3: Noise in Trotter Simulation

This repository is a Phase-1 online implementation built from the **Qiskit Fall Fest 2026 Phase 1 Quantum Processor & Architecture Starter Notebook** supplied with this project.

### Scope

The implementation follows the online Phase-1 workflow described in the supplied guide:

1. Select exactly one Problem Statement: **S3 — Noise in Trotter Simulation**.
2. Build a reproducible logical quantum workflow.
3. Run the same logical workload on Processor A and Processor B.
4. Inspect transpilation/routing effects.
5. Record problem and architecture/resource metrics.
6. Compare A vs B using tables and figures.
7. Explain the observed differences with measured evidence.
8. Report uncertainty, limitations and reproducibility information.
9. Keep the work limited to the online Phase-1 A/B study; no Phase-2 processor work is included.

The supplied guide does not define a complete S3 Hamiltonian, Trotter order, or final S3-specific instance. To keep the repository runnable without inventing organizer-specific data, the project contains:

- a **guide-inspired Bell practice benchmark** using the guide's Bell-state and measurement concepts; its processor graphs, noise rates and routing overhead are locally illustrative, not a recreation of the official Processor A/B models;
- a **minimal Trotter demonstrator** whose parameters are documented as an illustrative research model, not as an organizer-defined benchmark;
- an **optional Qiskit/Aer path** matching the code style shown in the guide;
- machine-readable results and figures that can be regenerated.

No demonstrator result is claimed as an official competition result.

> **Competition-readiness warning:** the current processor JSON files are local illustrative practice models, not the official Processor A/B definitions. The supplied geometry-aware challenge presentation describes Processor A as 5 qubits and Processor B as 7 qubits with a heavy-hex-inspired graph; this repository's practice models are both 5 qubits and use fully-connected/line graphs. Do not submit practice metrics as the required official A/B results. Replace the practice models only when the organizer-provided S3 Challenge Kit supplies the exact processor definitions, S3 instance, required outputs, and benchmark fields.

---

## Repository structure

```text
QFF2026_S3_Phase1_Project/
├── README.md
├── main.ipynb
├── requirements.txt
├── requirements-practice.txt
├── .gitignore
├── LICENSE
│
├── data/
│   ├── raw/
│   └── processed/
│
├── processors/
│   ├── processor_A.json
│   └── processor_B.json
│
├── src/
│   ├── __init__.py
│   ├── bell_benchmark.py
│   ├── metrics.py
│   ├── problem.py
│   ├── processors.py
│   ├── routing.py
│   └── visualization.py
│
├── scripts/
│   ├── build_notebook.py
│   ├── make_practice_figures.py
│   ├── run_bell_benchmark.py
│   ├── run_practice.py
│   └── validate_submission.py
│
├── tests/
│   ├── test_bell_benchmark.py
│   └── test_practice.py
│
├── results/
│   ├── tables/
│   └── figures/
│
├── report/
│   └── report.md
│
├── docs/
│   ├── phase1_scope.md
│   ├── pdf_requirements_matrix.md
│   └── github_setup.md
│
└── assets/
    └── qff_phase1_latex_images/
```

This matches the folder/file organization explicitly recommended by the supplied guide while keeping reusable source code separated from results and reporting.

---


## Official submission gate

The repository intentionally separates practice scaffolding from the official competition benchmark. The Phase-1 instructions require the selected problem's Challenge Kit, exact Processor A/B definitions, the specified inputs/outputs, and measured A-vs-B results before the submission can be treated as official.

Use the repository gate explicitly:

```bash
python scripts/validate_submission.py --practice

python scripts/validate_submission.py --official
```

The --official check is deliberately strict. It requires a local Challenge Kit manifest, verifies that the referenced kit files exist, rejects illustrative/toy processor definitions, and confirms that the repository has been promoted from guide-derived settings to kit-derived settings.

See docs/official_kit_integration.md for the exact integration sequence.

## Installation

### Standard Qiskit environment

```bash
python -m venv .venv
```

Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Linux/macOS:

```bash
source .venv/bin/activate
```

Then:

```bash
pip install -r requirements.txt
```

### Practice-only fallback environment

The core NumPy reference implementation can run without Qiskit:

```bash
pip install -r requirements-practice.txt
```

---

## Run the guide-inspired Bell practice benchmark

```bash
python scripts/run_bell_benchmark.py
```

This benchmark follows the guide's explicit Bell-state workflow and reports:

- XX correlation
- YY correlation
- ZZ correlation
- Bell-state fidelity
- uncertainty for proportion-like quantities where applicable
- circuit depth / gate counts for the logical circuit
- Processor A/B routing overhead
- physical qubits
- postselection yield for the protected experiment

The benchmark intentionally keeps the exact architecture/noise assumptions in explicit JSON processor files and documents them as illustrative project settings.

---

## Run the S3-style Trotter demonstrator

```bash
python scripts/run_practice.py
```

This is a minimal, self-contained research demonstrator for the S3 theme. It uses a small Hamiltonian, a first-order Trotter product formula, two illustrative processor geometries and a stochastic Pauli-error model.

The demonstrator is **not** a claim about any organizer-supplied S3 instance.

---

## Run the notebook

```bash
jupyter notebook main.ipynb
```

The notebook is organized around the guide's sections:

1. How to use the notebook
2. Phase-1 overview
3. Repository structure
4. Core mental model
5. Quantum foundations
6. Processor as a graph
7. Bell-state example
8. Routing and SWAP overhead
9. Transpilation
10. Noise
11. Required measurements
12. Processor definitions
13. Problem statement
14. A/B experiment
15. A/B comparison
16. Protection / error detection
17. Scientific reporting
18. Results and figures
19. Experience-level approaches
20. Workflow checklist
21. Final experiment structure
22. Submission checklist
23. Participant lab notes

---

## Run tests

```bash
pytest -q
```

## Validate repository structure

```bash
python scripts/validate_submission.py --practice
```

---

## Methodology

The core architecture mental model is:

```text
Problem / algorithm
        ↓
Logical quantum circuit
        ↓
Placement + routing + gate decomposition
        ↓
Physical processor
(qubits + coupling graph + gates + noise)
        ↓
Measurements
        ↓
Problem metric + architecture metrics
```

The project treats transpilation as part of the architecture story rather than an invisible implementation detail.

For the PDF-derived routing study, Processor B uses a line topology so that a long-range logical interaction requires additional routing. This lets the project quantify the impact on depth, two-qubit operations, routing overhead and noise exposure.

---

## Results organization

Machine-readable outputs are stored under:

```text
results/tables/
results/figures/
```

Example table files:

```text
processor_A_metrics.csv
processor_B_metrics.csv
AB_comparison.csv
final_comparison.csv
```

Example figures:

```text
logical_vs_transpiled.png
AB_performance.png
architecture_tradeoffs.png
```

Plots are generated from saved numerical data so they can be regenerated instead of relying on screenshots.

---

## Scientific reporting

Every reported result should preserve enough information to reproduce it, including when applicable:

- processor definition
- circuit version
- number of shots/trajectories
- random seed
- noise assumptions
- circuit depth
- two-qubit gate count
- routing/SWAP overhead
- qubit/ancilla usage
- postselection yield
- uncertainty

For a proportion estimated from independent shots, the supplied guide gives:

\[
\sigma_p \approx \sqrt{\frac{p(1-p)}{N}}.
\]

The project reports uncertainty rather than presenting a single quality number without experimental context.

---

## Interpretation framework

The final analysis should explicitly answer:

1. What changed?
2. Which architectural property changed?
3. Did transpilation introduce more routing?
4. How many extra operations appeared?
5. Did the problem metric change?
6. Could gate-set/noise differences also contribute?
7. What remains uncertain?

Conclusions must be tied to measured results rather than unsupported assumptions.

---

## Experience-level paths

The supplied guide describes three possible depth levels:

### Explorer
Bell preparation + simple error detection; compare ideal, noisy and protected results.

### Builder
Investigate placement/routing or improved checks; compare fidelity benefit against extra operations.

### Research
Investigate geometry-aware encodings or stabilizer networks; study scaling and noise sensitivity.

The default repository implements the **Builder** direction for the architecture study while keeping the S3 Trotter demonstrator compact and reproducible.

---

## AI disclosure

This repository was prepared with AI-assisted development. The submitting team must review every implementation detail, verify the results, understand the methods, and update the disclosure according to the hackathon's official AI-use requirements.

---

## Limitations

The supplied 26-page starter notebook provides the Phase-1 methodology, an illustrative 5-qubit line processor, a Bell-state example, routing/transpilation examples, an illustrative noise model, metrics, reporting requirements and repository guidance. It does not itself specify every scientific parameter required to define a unique S3 benchmark.

Therefore, all non-source numerical settings used by the runnable demonstrations are explicitly labeled **illustrative** and are separated from the repository's methodological structure.


## Engineering hardening

The runnable practice implementation includes strict configuration validation, topology-derived routing, statevector memory guards, online statistical accumulation, explicit readout-error handling, deterministic notebook generation and CI verification.

Validation modes:

~~~bash
python scripts/validate_submission.py --practice
python scripts/validate_submission.py --official
~~~

Practice validation checks the full runnable engineering scaffold and generated artifacts. Official validation intentionally fails closed until the organizer-supplied S3 Challenge Kit is integrated.
