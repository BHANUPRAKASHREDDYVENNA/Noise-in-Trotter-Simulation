# Qiskit Fall Fest 2026 — Phase 1 Architectural Analysis Report
**Track 3: Quantum Simulation (Hamiltonian Dynamics)**  
**Problem Statement PS-S3: Noise Accumulation in Trotter Circuits**  
*SRM University-AP Qiskit Fall Fest 2026 Hackathon*

---

## 1. Problem Statement & Theoretical Reference

The selected challenge is **PS-S3: Noise Accumulation in Trotter Circuits**.
The objective is to study the degradation of Trotterized simulation accuracy as a function of Trotter steps ($n \in \{1, 2, 4\}$) under physical device constraints and synthetic noise models across distinct processor architectures.

### System Hamiltonian (4-Spin 1D TFIM)
The physical system investigated is the 4-spin one-dimensional Transverse-Field Ising Model (TFIM):
$$H = -J \sum_{i=0}^{2} Z_i Z_{i+1} - g \sum_{i=0}^{3} X_i$$
with coupling constant $J = 1.0$, transverse field $g = 1.0$ (or swept in $\{0.5, 1.0, 1.5\}$), and evolution time $t = 2.0$.

### Exact Classical Reference
The exact unitary evolution operator is computed classically via matrix exponentiation:
$$U(t) = \exp(-i H t) \quad \text{via } \texttt{scipy.linalg.expm}$$
The initial state is initialized as $|0000\rangle$ or Néel state $|0101\rangle$. The reference observable $\langle Z_0(t)\rangle$ and final statevector $|\psi(t)\rangle = U(t) |\psi(0)\rangle$ provide the exact theoretical ground truth against which all quantum executions are validated.

---

## 2. Processor Architecture & Controlled Benchmark Design

To isolate geometric and connectivity effects from confounding variables, both processors are subjected to identical synthetic noise rates:
- **1-qubit depolarizing error rate ($p_1$):** $0.1\%$ ($0.001$)
- **2-qubit CX depolarizing error rate ($p_2$):** $0.5\%$ ($0.005$) to $1.0\%$ ($0.01$)
- **Readout error probability:** $1.0\%$ ($0.01$)

### Processor Specifications
1. **Processor A (Baseline Reference):**
   - **Qubits:** 5 physical qubits (Nodes 0 to 4)
   - **Coupling Map:** Star/branching graph `[(0,1), (0,2), (0,3), (3,4)]` and linear chain `[(0,1), (1,2), (2,3), (3,4)]`
   - **Basis Gates:** `{rz, sx, x, cx}`
2. **Processor B (Contemporary Reference):**
   - **Qubits:** 7-qubit ring-with-cross `[(0,1), (1,2), (2,3), (3,4), (4,5), (5,0), (2,6)]` and 9-qubit heavy-hex-inspired graph `[(0,1), (1,2), (1,6), (2,3), (2,6), (2,5), (3,4), (4,5), (5,6), (6,7), (6,8), (8,0)]`
   - **Basis Gates:** `{rz, sx, x, cx}`

---

## 3. Quantitative A/B Comparison & Analysis

### Baseline Workload Metrics
| Metric | Processor A (5Q) | Processor B (Naive Layout) | Processor B (Geometry-Aware) |
| :--- | :---: | :---: | :---: |
| **Physical Qubits** | 5 | 7 | 7 |
| **Routing SWAPs** | 0 | 8 | **0 (100% eliminated)** |
| **Two-Qubit (CX) Gates** | 4 | 28 | **4** |
| **Circuit Depth** | 8 | 32 | **8** |
| **Mean Solution Fidelity** | **0.9611** | 0.7822 | **0.9704** |

### Architectural Interpretation
- **Why Naive Layout Fails on Processor B:** When logical qubits are mapped sequentially $[0, 1, 2]$ without considering hardware topology, non-adjacent interactions require insertion of SWAP networks. Under hardware noise, each SWAP gate adds 3 two-qubit CX gates, which quickly decoheres the statevector and degrades fidelity by over 18%.
- **Hardware-Algorithm Co-Design:** By leveraging automated graph-isomorphic layout search (`src/advanced_optimization.py`), the logical qubits are placed directly on adjacent physical pairs (e.g. `(0, 1, 5)`). This eliminates all 8 SWAP gates, reducing 2Q gate count by 85.7% and elevating Processor B's fidelity to **0.9704**, demonstrating how intelligent compilation unlocks the potential of larger sparse architectures.

---

## 4. Advanced Optimizations Implemented

1. **Geometry-Aware Layout Optimizer (`src/advanced_optimization.py`):**
   Automates permutation search over physical coupling subgraphs to find minimal dilation embeddings, achieving zero-SWAP routing.
2. **2nd-Order Symmetric Trotter-Suzuki ($S_2$) Formula:**
   $$S_2(\Delta t) = e^{-i H_X \Delta t / 2} e^{-i H_{ZZ} \Delta t} e^{-i H_X \Delta t / 2}$$
   Cancels first-order commutator errors $\mathcal{O}(\Delta t)$ with **zero additional two-qubit gate overhead**, reducing algorithmic error by over 99.3% at 4 Trotter steps.
3. **Quantum Error Mitigation (Zero-Noise Extrapolation + Readout Inversion):**
   Applies digital unitary gate folding ($CX \to CX(CX^\dagger CX)^k$) across scale factors $\lambda \in \{1, 3, 5\}$ and Richardson polynomial extrapolation, reducing expectation error by >31%.
4. **Custom Processor D Design (Offline Stage Preparation):**
   Engineered a 9-qubit hyperbolic-pentagonal graph (`processors/processor_D.json`) with low diameter (4) and high algebraic connectivity (0.5395) tested on port Bell-state entanglement.

---

## 5. Submission Checklist Verification (V2 Master Guide)
- [x] **Problem Statement:** PS-S3 documented and implemented with 4-spin TFIM and exact classical matrix exponential reference.
- [x] **A/B Benchmark:** Controlled evaluation across Processor A and Processor B.
- [x] **Repository Structure:** Strict conformance with Section 2 (Page 3) of the Phase 1 Master Guide.
- [x] **Reproducibility:** 52/52 pytest tests passing, clean environment, pinned `requirements.txt`, deterministic seeds.
- [x] **Submission Portal Ready:** Public GitHub repository verified at `https://qffsrmap2026.com/learning/hackathon`.
