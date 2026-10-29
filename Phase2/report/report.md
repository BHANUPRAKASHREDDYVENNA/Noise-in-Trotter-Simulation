# PS-S3 Phase 2 Final Technical & Scientific Report
## Track 3: Quantum Simulation (Hamiltonian Dynamics)
### Problem Statement PS-S3: Noise Accumulation in Trotter Circuits

---

**Partner Plus IBM Qiskit Fall Fest 2026 — Phase 2 On-Campus Hackathon**  
*Auditorium & X-Lab, SRM University-AP, Andhra Pradesh, India*  
**Date of Submission:** 29–30 October 2026  
**Team Name:** `QUANTUM'S`  
**Team Lead:** **Bhanu Prakash Venna**  
**Affiliation:** Department of Computer Science & Engineering, SRM University-AP  
**Public Repository:** [https://github.com/BHANUPRAKASHREDDYVENNA/Noise-in-Trotter-Simulation](https://github.com/BHANUPRAKASHREDDYVENNA/Noise-in-Trotter-Simulation)  
**Portal Submission:** [https://www.qffsrmap2026.com/learning/hackathon](https://www.qffsrmap2026.com/learning/hackathon)

---

## Executive Summary & Headline Discoveries

This report presents the definitive, experimentally validated solution for **Problem Statement PS-S3: Noise Accumulation in Trotter Circuits** under the official Phase 2 Hackathon specification. Investigating the quantum dynamics of a 4-spin one-dimensional Transverse-Field Ising Model (TFIM) on a **periodic ring** evolved to $T = 2.0$, we resolve the fundamental competition between algorithmic Trotter discretization error and physical device noise accumulation.

### Key Quantitative Findings:
1. **The Trotter-Noise Crossover ($n^*$):**  
   Across a 12-point Trotter step grid $n \in \{1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16\}$, we definitively confirm the existence of an optimal step count $n^* = 7$ for native-cycle architectures (Processors B and D) under official standard noise ($p_1=0.001, p_2=0.005, p_{\rm ro}=0.01$), achieving a peak density-matrix state fidelity $\mathcal{F}^* = 0.6628$.
2. **Noise Scaling Dynamics on Custom Processor D:**  
   Sweeping the noise scaling factor directly validates the theoretical scaling of the crossover point:
   - **Low Noise ($0.5\times$):** Discretization error dominates longer, shifting the optimum upward to **$n^* = 8$** with peak fidelity **$\mathcal{F}^* = 0.7821$**.
   - **Standard Noise ($1.0\times$):** Balanced regime yields **$n^* = 7$** with peak fidelity **$\mathcal{F}^* = 0.6628$**.
   - **High Noise ($2.0\times$):** Physical gate errors accumulate twice as fast, suppressing deep circuits and shifting the optimum downward to **$n^* = 6$** with peak fidelity **$\mathcal{F}^* = 0.5031$**.
3. **Topological Penalty on Tree Graphs (Processor A):**  
   Processor A (5-qubit tree baseline) lacks a 4-cycle. Simulating the periodic boundary condition bond $(3, 0)$ requires routing SWAP networks (11 SWAP gates / 33 routing CX gates at $n=6$), exploding two-qubit depth from 24 to 57 and depressing peak fidelity to **$0.5774$** (an absolute degradation of $8.54\%$ and relative loss of $12.89\%$ compared to Processor D).
4. **Custom Processor D Co-Design:**  
   Our 9-qubit cubic hypercube hybrid architecture embeds native 4-cycles with diameter 3, average path length 1.778, and maximum degree 4. It executes the ring TFIM with **zero routing SWAPs**, passing all official constraints verified by `tools/check_processor_d.py`.
5. **Entanglement Verification (Objective 1):**  
   Bell-state parity measurements on Processor D yield $\mathcal{F} = 0.9633 \pm 0.0021$ on adjacent pair $(0, 1)$ ($d=1$, 1 CX) and $\mathcal{F} = 0.9476 \pm 0.0025$ on distant pair $(0, 6)$ ($d=3$, 7 CX due to 2 routing SWAPs).
6. **Error Mitigation Advantage (Bonus):**  
   Digital Zero-Noise Extrapolation (ZNE) via unitary gate folding ($\lambda \in [1, 3, 5]$) recovers the unmitigated staggered magnetization from $M_s = 0.4403$ (error $0.2121$) to $M_s^{\rm ZNE} = 0.4971$ (error $0.1553$), demonstrating a **$>26.8\%$ error reduction**.

---

## 1. Problem Statement & Theoretical Formulation

### 1.1 The Physical Hamiltonian: 4-Spin Periodic Ring TFIM
The physical system investigated is the one-dimensional Transverse-Field Ising Model (TFIM) on a closed periodic ring of $N = 4$ spin-1/2 particles:
$$H = -J \sum_{i=0}^{N-1} Z_i Z_{i+1} - g \sum_{i=0}^{N-1} X_i$$
with periodic boundary conditions identifying index $N \equiv 0$. The four interacting nearest-neighbor bonds are:
$$\mathcal{E}_{\rm ring} = \{(0, 1), (1, 2), (2, 3), (3, 0)\}$$
In accordance with the locked challenge specification (`data/s3/tfim_ring_N4_g1.00.json`), the system parameters are:
- Spin chain size: $N = 4$ qubits (Hilbert space dimension $2^4 = 16$).
- Nearest-neighbor Ising exchange coupling: $J = 1.0$.
- Transverse external magnetic field: $g = 1.0$ (critical point of the infinite chain).
- Target simulation time: $T = 2.0$.
- Initial state: Néel antiferromagnetic state $|\psi(0)\rangle = |1010\rangle$ ($Z_i = (-1)^i$).

### 1.2 Exact Classical Ground Truth
The exact unitary evolution operator is computed classically via matrix exponentiation of the full $16 \times 16$ sparse Hamiltonian:
$$|\psi_{\rm exact}(T)\rangle = \exp(-i H T) |\psi(0)\rangle$$
The exact target observable is the staggered magnetization:
$$M_s(T) = \frac{1}{N} \sum_{i=0}^{N-1} (-1)^i \langle \psi(T) | Z_i | \psi(T) \rangle$$
At $T = 2.0$, classical diagonalization yields the exact reference value:
$$M_s^{\rm exact}(T = 2.0) = 0.652444$$

### 1.3 Algorithmic Discretization: First-Order Lie-Trotter Formula
Because the transverse field operator $H_X = -g \sum_i X_i$ and the Ising interaction operator $H_{ZZ} = -J \sum_i Z_i Z_{i+1}$ do not commute ($[H_{ZZ}, H_X] \neq 0$), the exponential cannot be evaluated as a single product. Under the first-order Lie-Trotter product formula, the total evolution time $T$ is divided into $n$ discrete time steps of duration $\Delta t = T / n$:
$$U_1(T) = \left[ U_1(\Delta t) \right]^n = \left[ \prod_{i=0}^3 e^{i g \Delta t X_i} \prod_{(j, k) \in \text{even}} e^{i J \Delta t Z_j Z_k} \prod_{(l, m) \in \text{odd}} e^{i J \Delta t Z_l Z_m} \right]^n$$
In each step:
1. Single-qubit rotations: $R_X(2 g \Delta t)$ applied to all qubits $i \in \{0, 1, 2, 3\}$.
2. Even-bond two-qubit interactions: $R_{ZZ}(2 J \Delta t)$ applied on bonds $(0, 1)$ and $(2, 3)$.
3. Odd-bond two-qubit interactions: $R_{ZZ}(2 J \Delta t)$ applied on bonds $(1, 2)$ and $(3, 0)$.

Each two-qubit $R_{ZZ}(\theta)$ gate is synthesized into the native hardware basis $\{CX, RZ, SX, X\}$ using the canonical two-CX decomposition:
$$R_{ZZ}(\theta) = CX(q_j, q_k) \cdot R_Z(\theta, q_k) \cdot CX(q_j, q_k)$$
Thus, each Trotter step requires exactly $4 \text{ bonds} \times 2 \text{ CX/bond} = 8 \text{ logical CX gates}$.

### 1.4 The Trotter-Noise Trade-off Mechanism
The total simulation error $\epsilon(n)$ is governed by two opposing physical mechanisms:
$$\epsilon_{\rm total}(n) \approx \epsilon_{\rm Trotter}(n) + \epsilon_{\rm noise}(n)$$
1. **Algorithmic Discretization Error ($\epsilon_{\rm Trotter}$):**  
   The Baker-Campbell-Hausdorff (BCH) expansion shows that first-order Trotterization introduces a leading error term proportional to the commutator:
   $$\epsilon_{\rm Trotter}(n) \le \frac{T^2}{2 n} \sum_{i < j} \| [H_i, H_j] \| = \mathcal{O}\left(\frac{T^2}{n}\right)$$
   As $n \to \infty$, algorithmic error decreases monotonically toward zero.
2. **Physical Gate Noise Accumulation ($\epsilon_{\rm noise}$):**  
   On physical quantum processors, every two-qubit CX gate is subject to depolarizing error $p_2$. For $n$ Trotter steps with $N_{\rm CX}(n)$ two-qubit gates, the total state fidelity decays exponentially:
   $$\mathcal{F}_{\rm noise}(n) \approx (1 - p_2)^{N_{\rm CX}(n)} \approx 1 - n \cdot N_{\rm CX/step} \cdot p_2$$
   Thus, noise accumulation scales linearly with $n$:
   $$\epsilon_{\rm noise}(n) = \mathcal{O}(n \cdot N_{\rm CX/step} \cdot p_2)$$

The interplay creates a convex fidelity curve $\mathcal{F}(n)$ with an optimal sweet spot $n^*$:
$$\frac{\partial \epsilon_{\rm total}}{\partial n} = 0 \implies n^* \propto T \sqrt{\frac{\sum \|[H_i, H_j]\|}{2 \cdot N_{\rm CX/step} \cdot p_2}}$$
Finding and characterizing $n^*$ across hardware topologies is the central mission of PS-S3.

---

## 2. Objective 1: Bell-State Verification on Processor D

Before executing multi-qubit dynamical simulation, the physical fidelity of two-qubit entanglement must be verified on custom Processor D.

### 2.1 State Preparation and Measurement Methodology
We prepare the canonical maximally entangled Bell state:
$$|\Phi^+\rangle = \frac{1}{\sqrt{2}}(|00\rangle + |11\rangle)$$
State preparation uses a Hadamard gate followed by a two-qubit CNOT gate: $|\Phi^+\rangle = CX(H \otimes I)|00\rangle$.

We evaluate two physical qubit pairs on Processor D:
- **Near Pair:** Physical qubits `(0, 1)` with topological distance $d=1$ (directly connected edge).
- **Far Pair:** Physical qubits `(0, 6)` with topological distance $d=3$ (furthest separation on the 9-qubit graph).

For each pair, two-qubit parity correlations are measured along three mutually orthogonal Pauli bases ($XX$, $YY$, and $ZZ$) with $N = 4,096$ shots per basis:
- **$ZZ$ Basis:** Computational basis measurement without basis rotation.
- **$XX$ Basis:** Hadamard rotation $H$ applied to both qubits prior to measurement.
- **$YY$ Basis:** Phase-Hadamard rotation $S^\dagger H$ applied to both qubits prior to measurement.

### 2.2 Mathematical Formulas for Fidelity & Error Propagation
The expectation value of each two-qubit parity operator $P \in \{XX, YY, ZZ\}$ is computed from the even and odd shot outcomes:
$$\langle P \rangle = \frac{N_{\rm even} - N_{\rm odd}}{N_{\rm total}} = \frac{N_{00} + N_{11} - N_{01} - N_{10}}{N}$$
The sample standard error of the mean for each observable is given by the binomial variance:
$$\mathrm{SE}(\langle P \rangle) = \sqrt{\frac{1 - \langle P \rangle^2}{N}}$$
The state fidelity with respect to the ideal Bell state $|\Phi^+\rangle$ is reconstructed via quantum state tomography reduction:
$$\mathcal{F} = \langle \Phi^+ | \rho | \Phi^+ \rangle = \frac{1 + \langle XX \rangle - \langle YY \rangle + \langle ZZ \rangle}{4}$$
By standard Gaussian error propagation, the standard error of the estimated fidelity is:
$$\mathrm{SE}(\mathcal{F}) = \frac{1}{4} \sqrt{\left(\mathrm{SE}_{XX}\right)^2 + \left(\mathrm{SE}_{YY}\right)^2 + \left(\mathrm{SE}_{ZZ}\right)^2}$$

### 2.3 Experimental Results & Hardware Interpretation

Table 1 compiles the complete experimental results generated in `results/tables/bell.csv`:

| Pair | Label | Distance | Mode | $\langle XX \rangle \pm \mathrm{SE}$ | $\langle YY \rangle \pm \mathrm{SE}$ | $\langle ZZ \rangle \pm \mathrm{SE}$ | Bell Fidelity $\mathcal{F} \pm \mathrm{SE}$ | 2Q Gates |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `(0, 1)` | near | 1 | ideal | $1.0000 \pm 0.0000$ | $-1.0000 \pm 0.0000$ | $1.0000 \pm 0.0000$ | **$1.0000 \pm 0.0000$** | 1 |
| `(0, 1)` | near | 1 | noisy | $0.9497 \pm 0.0049$ | $-0.9507 \pm 0.0048$ | $0.9531 \pm 0.0047$ | **$0.9633 \pm 0.0021$** | 1 |
| `(0, 6)` | far | 3 | ideal | $1.0000 \pm 0.0000$ | $-1.0000 \pm 0.0000$ | $1.0000 \pm 0.0000$ | **$1.0000 \pm 0.0000$** | 7 |
| `(0, 6)` | far | 3 | noisy | $0.9312 \pm 0.0057$ | $-0.9341 \pm 0.0056$ | $0.9258 \pm 0.0059$ | **$0.9476 \pm 0.0025$** | 7 |

> **Physical Analysis:**
> 1. **Near Pair `(0, 1)` ($d=1$):** Because qubits 0 and 1 share a direct physical edge, the transpiler compiles the state using a single CX gate. The noisy fidelity of $0.9633 \pm 0.0021$ reflects the baseline limit imposed by single-qubit gate errors ($p_1 = 0.001$), one two-qubit gate depolarizing error ($p_2 = 0.005$), and independent bit-flip readout errors ($p_{\rm ro} = 0.01$).
> 2. **Far Pair `(0, 6)` ($d=3$):** Qubits 0 and 6 are separated by 3 hops. The SABRE routing pass routes the interaction along the shortest geodesic path by inserting 2 intermediate SWAP gates. Because each SWAP gate decomposes into 3 CX gates, the circuit executes $1 + 2 \times 3 = 7$ two-qubit CX gates. The 6 additional CX gates inject an extra $\approx 6 \times p_2 = 3.0\%$ depolarizing noise, reducing the Bell state fidelity to $0.9476 \pm 0.0025$. This verifies the predictable degradation of entanglement as a function of graph distance.

---

## 3. Objective 2: Custom Processor D Architectural Co-Design

### 3.1 Hardware Topology & Graph Invariants
Processor D is designed in `processors/processor_D.json` to eliminate the connectivity bottlenecks observed in existing baseline processors. Its architecture is derived from a 3-dimensional binary hypercube (8-vertex cubic graph) augmented with an ancillary readout/bus node.

```
       3 ------- 2
      /|        /|
     / |       / |
    7 ------- 6  |
    |  0 -----|- 1
    | /       | /     [Node 8: readout bus connected to 0 and 4]
    |/        |/
    4 ------- 5
```

- **Physical Qubits ($V$):** 9 vertices $\{0, 1, 2, 3, 4, 5, 6, 7, 8\}$.
- **Physical Couplers ($E$):** 14 undirected edges:
  `[[0, 1], [1, 2], [2, 3], [3, 0], [4, 5], [5, 6], [6, 7], [7, 4], [0, 4], [1, 5], [2, 6], [3, 7], [0, 8], [4, 8]]`.
- **Maximum Node Degree:** $\Delta(G) = 4$ (at nodes 0 and 4).
- **Graph Diameter:** $\mathrm{diam}(G) = 3$.
- **Average Shortest Path Length:** $\bar{d} = 1.778$.
- **Basis Gates:** `{rz, sx, x, cx}`.
- **Physical Error Rates:** $p_1 = 0.001, p_2 = 0.005, p_{\rm ro} = 0.01$.

### 3.2 Topological Advantage over Processors A and B
1. **Processor A (5Q Star/Tree):** Processor A contains a central hub (Node 0) with peripheral leaves. It possesses no closed loops ($C_4 = 0$). When simulating any cyclic Hamiltonian like the periodic ring TFIM, closing the final bond $(3, 0)$ requires routing states back through the tree, forcing multiple SWAP gates per Trotter step.
2. **Processor B (Heavy-Hex Topology):** Processor B features sparse hexagonal connectivity with low maximum degree (3). While it contains large cycles, mapping a compact 4-spin ring often introduces routing dilation if the layout does not align with a native 4-cycle.
3. **Processor D (Cubic Hybrid Architecture):** Processor D embeds the 4-cycle `[(0, 1), (1, 2), (2, 3), (3, 0)]` directly on its front face. Any 4-spin ring Hamiltonian can be placed on these vertices with **zero routing SWAPs**, while the auxiliary couplers provide shortcuts that maintain a graph diameter of only 3 across all 9 qubits.

### 3.3 Official Schema Conformance & Validation
The configuration file `processors/processor_D.json` was validated using the official checker:
```bash
python tools/check_processor_d.py processors/processor_D.json 4
```
**Checker Output:**
```
OK - Processor D satisfies all design rules.
```
All criteria (valid JSON, required keys `num_qubits`, `basis_gates`, `edges`, `error_rates`, `justification`, $\ge 4$ qubits, connected graph, max degree $\le 4$, non-empty justification) are 100% satisfied.

---

## 4. Objective 3: Trotter Step Scan & Crossover Dynamics ($n^*$)

### 4.1 Benchmark Grid & Execution Protocol
We evaluate the 4-spin periodic ring TFIM across a comprehensive 12-point Trotter step count grid:
$$n \in \{1, 2, 3, 4, 5, 6, 7, 8, 10, 12, 14, 16\}$$
Five distinct benchmark configurations are evaluated across the 12 steps (60 full circuit evaluations):
1. **Processor A Baseline ($1.0\times$ Noise):** 5-qubit tree architecture.
2. **Processor B Baseline ($1.0\times$ Noise):** 9-qubit heavy-hex architecture.
3. **Processor D Proposed ($1.0\times$ Noise):** 9-qubit custom cubic hybrid architecture.
4. **Processor D Low Noise ($0.5\times$ Noise):** Physical error rates scaled by $0.5\times$ ($p_1=0.0005, p_2=0.0025, p_{\rm ro}=0.005$).
5. **Processor D High Noise ($2.0\times$ Noise):** Physical error rates scaled by $2.0\times$ ($p_1=0.002, p_2=0.010, p_{\rm ro}=0.020$).

For every circuit, we compute:
- **Noisy Density-Matrix State Fidelity:**  
  $$\mathcal{F}(n) = \langle \psi_{\rm exact}(T) | \rho_{\rm noisy}(n) | \psi_{\rm exact}(T) \rangle$$
- **Ideal Discretization State Fidelity:**  
  $$\mathcal{F}_{\rm ideal}(n) = |\langle \psi_{\rm exact}(T) | \psi_{\rm ideal}(n) \rangle|^2$$
- **Noisy Staggered Magnetization:**  
  $$M_s(n) = \frac{1}{4} \sum_{i=0}^3 (-1)^i \langle Z_i(n) \rangle_{\rm noisy} \pm \mathrm{SE}$$
- **Hardware Resources:** Transpiled two-qubit gate count (logical vs SWAP), circuit depth, and active physical qubits.

### 4.2 Summary of Optimal Step Counts ($n^*$)

Table 2 presents the definitive crossover summary from `results/tables/s3_summary.csv`:

| Configuration | Noise Scale | Native 4-Cycle? | Routing SWAPs | Optimal Steps $n^*$ | Peak Fidelity $\mathcal{F}^*$ | Ideal Trotter Fidelity | Noisy $M_s(n^*)$ |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Processor A** | $1.0\times$ | No (Tree) | **11** | **6** | **0.5774** | 0.9934 | $0.4131 \pm 0.0142$ |
| **Processor B** | $1.0\times$ | Yes | **0** | **7** | **0.6628** | 0.9951 | $0.4403 \pm 0.0141$ |
| **Processor D** | $1.0\times$ | Yes | **0** | **7** | **0.6628** | 0.9951 | $0.4403 \pm 0.0141$ |
| **Processor D** | $0.5\times$ | Yes | **0** | **8** | **0.7821** | 0.9963 | $0.5361 \pm 0.0132$ |
| **Processor D** | $2.0\times$ | Yes | **0** | **6** | **0.5031** | 0.9934 | $0.3242 \pm 0.0148$ |

*(Note: Exact classical staggered magnetization $M_s^{\rm exact} = 0.652444$.)*

### 4.3 Detailed Physical Analysis of the Crossover

#### 1. The Low-Step Regime ($n \in \{1, 2, 3, 4\}$): Algorithmic Error Dominance
At $n=1$, the time step $\Delta t = 2.0$ is large, resulting in massive commutator truncation error. The ideal Trotter fidelity is only $\mathcal{F}_{\rm ideal} = 0.5029$. Even under zero noise, the simulation deviates radically from the true dynamics. As $n$ increases to 4, $\mathcal{F}_{\rm ideal}$ surges from $0.5029 \to 0.9760$. In this regime, the benefit of reducing discretization error far outweighs the modest noise incurred by executing $8 \times n$ gates. Consequently, the noisy fidelity $\mathcal{F}_{\rm noisy}$ rises sharply.

#### 2. The Crossover Sweet Spot ($n^* \in \{6, 7, 8\}$):
Between $n=5$ and $n=8$, algorithmic discretization error drops below $1\%$ ($\mathcal{F}_{\rm ideal} > 0.99$). At this transition point, the marginal gain from further reducing Trotter error is smaller than the marginal fidelity loss caused by adding another 8 noisy CX gates ($8 \times p_2 = 4.0\%$ per step). This forms a distinct convex maximum:
- On Processor D at $1.0\times$ noise, peak fidelity occurs at **$n^* = 7$** with $\mathcal{F} = 0.6628$.
- On Processor A, because 11 routing SWAPs add 33 extra CX gates, noise accumulates much faster, pulling the optimum down to **$n^* = 6$** with a severely degraded peak $\mathcal{F} = 0.5774$.

#### 3. The High-Step Regime ($n \ge 10$): Decoherence Catastrophe
Beyond $n=8$, discretization error is essentially eliminated ($\mathcal{F}_{\rm ideal} \ge 0.998$). However, circuit depth and gate count continue to scale linearly with $n$. At $n=16$, the circuit executes 128 CX gates on Processor D and 239 CX gates on Processor A. Under continuous depolarizing noise, the density matrix progressively mixes toward the maximally mixed state $\mathbb{I}/16$. By $n=16$, fidelity collapses to $\mathcal{F} = 0.4484$ on Processor D and $\mathcal{F} = 0.3015$ on Processor A.

### 4.4 Noise Scaling Dynamics ($0.5\times, 1.0\times, 2.0\times$)
The noise sweep on Processor D validates our analytical scaling model:
- When physical noise is reduced to **$0.5\times$**, the noise slope is cut in half. The circuit can execute more Trotter steps before noise overtakes discretization error. The peak shifts rightward to **$n^* = 8$**, and maximum fidelity reaches **$0.7821$** ($+11.93\%$ higher than baseline).
- When physical noise is doubled to **$2.0\times$**, gate errors accumulate rapidly. Each step introduces an effective $8 \times 0.010 = 8.0\%$ gate error. The threshold where noise exceeds Trotter gains is reached earlier, shifting the peak leftward to **$n^* = 6$** and dropping maximum fidelity to **$0.5031$** ($-15.97\%$ lower than baseline).

---

## 5. Objective 4: Hardware Resource Accounting & Gate Budget

A rigorous evaluation of quantum simulation requires accounting for both logical circuit requirements and transpilation overhead.

### 5.1 Logical vs Routing Gate Decomposition
Every Trotter step of the 4-spin periodic ring TFIM requires:
- 4 single-qubit $R_X$ rotations.
- 4 two-qubit $R_{ZZ}$ interactions, synthesized as $4 \times 2 = 8$ logical CX gates.

Any CX gates in excess of $8 \times n$ represent **routing SWAP overhead** injected by the transpiler to move quantum information across non-adjacent physical qubits:
$$N_{\rm CX}^{\rm total} = N_{\rm CX}^{\rm logical} + N_{\rm CX}^{\rm routing} = 8n + 3 \times N_{\rm SWAP}$$

Table 3 compiles the complete resource accounting across representative step counts from `results/tables/resources.csv`:

| Processor | Steps $n$ | Total Depth | 2Q Depth | Total CX | Logical CX | Routing SWAP CX | SWAP Count | Active Qubits |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Processor A (5Q)** | 1 | 18 | 9 | **14** | 8 | **6** | **2** | 4 |
| **Processor A (5Q)** | 4 | 69 | 36 | **56** | 32 | **24** | **8** | 4 |
| **Processor A (5Q)** | 6 ($n^*$) | 110 | 57 | **81** | 48 | **33** | **11** | 4 |
| **Processor A (5Q)** | 8 | 137 | 71 | **115** | 64 | **51** | **17** | 4 |
| **Processor A (5Q)** | 16 | 280 | 145 | **239** | 128 | **111** | **37** | 4 |
| **Processor B (9Q)** | 1 | 11 | 6 | **8** | 8 | **0** | **0** | 4 |
| **Processor B (9Q)** | 4 | 41 | 24 | **32** | 32 | **0** | **0** | 4 |
| **Processor B (9Q)** | 7 ($n^*$) | 71 | 42 | **56** | 56 | **0** | **0** | 4 |
| **Processor B (9Q)** | 8 | 81 | 48 | **64** | 64 | **0** | **0** | 4 |
| **Processor B (9Q)** | 16 | 161 | 96 | **128** | 128 | **0** | **0** | 4 |
| **Processor D (9Q)** | 1 | 11 | 6 | **8** | 8 | **0** | **0** | 4 |
| **Processor D (9Q)** | 4 | 41 | 24 | **32** | 32 | **0** | **0** | 4 |
| **Processor D (9Q)** | 7 ($n^*$) | 71 | 42 | **56** | 56 | **0** | **0** | 4 |
| **Processor D (9Q)** | 8 | 81 | 48 | **64** | 64 | **0** | **0** | 4 |
| **Processor D (9Q)** | 16 | 161 | 96 | **128** | 128 | **0** | **0** | 4 |

### 5.2 Architectural Implications of the Gate Split
- **The Tree Topology Bottleneck on Processor A:**  
  On Processor A, the physical coupling graph has no cycles. To couple logical qubits 3 and 0 for the closing bond of the ring, the transpiler must execute routing SWAPs. At $n^* = 6$, Processor A incurs 11 SWAP gates (33 additional CX gates), increasing the total CX count from 48 to 81 ($+68.75\%$ overhead!). This expands two-qubit depth from 24 to 57 and suppresses peak fidelity by over $12.8\%$ relative to Processor D.
- **Zero Routing Overhead on Processors B and D:**  
  Because both Processor B and Processor D possess native cycles matching the 4-qubit interaction graph, the SABRE layout algorithm maps the 4 logical qubits directly onto a physical 4-cycle with zero dilation. Across all step counts $n \in \{1..16\}$, exactly $0$ SWAP gates are inserted. Total CX count remains strictly equal to the theoretical minimum $8n$.

---

## 6. Bonus: Quantum Error Mitigation (Zero-Noise Extrapolation)

To further enhance the fidelity of simulated observables without hardware modifications, we implemented **Zero-Noise Extrapolation (ZNE)** via digital unitary gate folding.

### 6.1 Mitigation Methodology & Gate Folding
Under digital gate folding, every two-qubit CX gate in the transpiled circuit is systematically replaced with an odd number of self-inverse gates:
$$CX \longrightarrow CX \cdot \left( CX^\dagger \cdot CX \right)^k$$
Because $CX \cdot CX = \mathbb{I}$ in the ideal unitary limit, this transformation leaves the logical circuit operator unchanged:
$$U_{\rm logical}(\lambda) = U_{\rm logical}(1)$$
However, under physical depolarizing noise, each folded gate incurs an independent physical error. The effective noise scale factor is:
$$\lambda = 2k + 1 \quad \text{for } k \in \{0, 1, 2\} \implies \lambda \in \{1, 3, 5\}$$
- $\lambda = 1$: Standard circuit ($k=0$, 56 CX gates).
- $\lambda = 3$: Folded circuit ($k=1$, 168 CX gates).
- $\lambda = 5$: Folded circuit ($k=2$, 280 CX gates).

### 6.2 Richardson Extrapolation to the Zero-Noise Limit
Expectation values $\langle M_s(\lambda) \rangle$ are measured at each noise scale $\lambda \in \{1, 3, 5\}$ with $N = 4,096$ shots per scale ($12,288$ shots total). We then fit a linear Richardson extrapolation model:
$$M_s(\lambda) = M_s^{\rm ZNE} + \alpha \lambda$$
Evaluating the regression at the unphysical zero-noise limit $\lambda \to 0$ yields the error-mitigated estimator $M_s^{\rm ZNE}$.

### 6.3 Quantitative Mitigation Results

Table 4 displays the results generated in `results/tables/mitigation.csv`:

| Noise Scale $\lambda$ | $k$ | Total CX Gates | Measured $M_s \pm \mathrm{SE}$ | Extrapolated $M_s^{\rm ZNE}$ | Exact Ground Truth $M_s$ | Absolute Error | Relative Error Reduction | Extra Shots |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| $\lambda = 1$ (Raw) | 0 | 56 | $0.4403 \pm 0.0141$ | — | $0.652444$ | $0.2121$ | Baseline | 0 |
| $\lambda = 3$ | 1 | 168 | $0.3276 \pm 0.0148$ | — | $0.652444$ | $0.3248$ | — | 4,096 |
| $\lambda = 5$ | 2 | 280 | $0.2114 \pm 0.0152$ | — | $0.652444$ | $0.4410$ | — | 8,192 |
| **$\lambda \to 0$ (Mitigated)** | — | — | — | **$0.4971$** | **$0.652444$** | **$0.1553$** | **$> 26.8\%$** | 8,192 |

> **Conclusion on Error Mitigation:**
> Digital gate folding successfully cancels first-order depolarizing noise. The unmitigated observable error of $0.2121$ is reduced to $0.1553$, recovering over **$26.8\%$** of the lost magnetization accuracy at a modest cost of $8,192$ additional measurement shots.

---

## 7. Comprehensive Submission Evidence & Scientific Artifacts

All benchmark tables and high-resolution figures have been generated and validated:

### 7.1 Quantitative Data Tables (`results/tables/`)
1. `results/tables/bell.csv`: Objective 1 Bell-state parity measurements, distances, and fidelities for near and far pairs on Processor D.
2. `results/tables/s3_scan.csv`: Full 60-row benchmark scan covering $n \in \{1..16\}$ across Processors A, B, D ($1.0\times$), D ($0.5\times$), and D ($2.0\times$).
3. `results/tables/s3_summary.csv`: Optimal Trotter step counts $n^*$, peak fidelities, and observable errors across all configurations.
4. `results/tables/resources.csv`: Hardware resource decomposition (depth, 2Q depth, CX split into logical vs routing SWAPs).
5. `results/tables/mitigation.csv`: Zero-Noise Extrapolation gate folding metrics, shot budgets, and error reduction percentages.

### 7.2 Publication-Grade Figures (`results/figures/`)
1. `results/figures/s3_fidelity_crossover.png`: Dual-panel publication figure illustrating density-matrix state fidelity crossover $\mathcal{F}(n)$ and staggered magnetization $M_s(n)$ across Processors A, B, and D.
2. `results/figures/s3_noise_sweep_D.png`: Shift in $n^*$ on Processor D under $0.5\times$, $1.0\times$, and $2.0\times$ noise scaling.
3. `results/figures/s3_gate_split.png`: Two-qubit gate budget showing the routing SWAP penalty on Processor A vs zero-SWAP execution on Processors B and D.
4. `results/figures/bell_correlations_D.png`: Parity correlation bars and state tomography fidelity for near vs far pairs on Processor D.
5. `results/figures/s3_zne_mitigation.png`: Zero-Noise Extrapolation linear fit showing raw vs mitigated magnetization.
6. `results/figures/processor_topologies.png`: Graph-theoretic topology comparison of Processor A (tree), Processor B (heavy-hex), and Processor D (cubic hybrid).

---

## 8. Verification, Testing & Reproducibility Protocol

### 8.1 Automated Test Suite Verification
The complete test suite is verified via `pytest`:
```bash
python -m pytest -q
```
**Test Result:** `58 passed in 9.08s` (100% pass rate, 0 failures, 0 warnings).

The test suite includes:
- `tests/test_phase2_s3.py`: Validates Processor D invariants, Bell parity math, Trotter Hamiltonian ring bonds, $n^*$ crossover bounds, noise scaling shifts, and ZNE monotonicity.
- `tests/test_processor_d.py` & `tools/check_processor_d.py`: Official design rule verification.
- `tests/test_advanced_optimization.py`, `tests/test_integration.py`, `tests/test_circuit_transpilation.py`, `tests/test_error_mitigation.py`: Legacy contract verification.

### 8.2 Exact Execution Commands for Independent Verification
Any reviewer or evaluator can reproduce the entire Phase 2 submission from scratch with the following commands:

```bash
# 1. Clone repository
git clone https://github.com/BHANUPRAKASHREDDYVENNA/Noise-in-Trotter-Simulation.git
cd Noise-in-Trotter-Simulation

# 2. Install dependencies
pip install -r requirements.txt

# 3. Validate Processor D design rules
python tools/check_processor_d.py processors/processor_D.json 4

# 4. Run complete Phase 2 benchmark pipeline (generates all CSV tables in results/tables/)
python scripts/run_phase2_s3.py

# 5. Generate all publication figures (saved in results/figures/)
python scripts/make_phase2_figures.py

# 6. Execute automated quality gate tests
python -m pytest -q

# 7. Run master notebook
jupyter nbconvert --to notebook --execute main.ipynb
```

---

## 9. Conclusion & Hackathon Submission Readiness

The **`QUANTUM'S`** team has completed every required objective and bonus item for **Problem Statement PS-S3**:
- **Objective 1:** Formally completed with Bell-state parity measurements and distance-scaling analysis.
- **Objective 2:** Completed with schema-compliant, checker-verified 9-qubit Processor D design.
- **Objective 3:** Fully completed with 60-circuit benchmark scan and theoretical explanation of $n^*$ crossover dynamics.
- **Objective 4:** Fully completed with explicit gate budget decomposition and routing SWAP penalty analysis.
- **Bonus:** Fully completed with Zero-Noise Extrapolation recovering $>26.8\%$ observable error.

The solution is 100% reproducible, scientifically rigorous, and immediately ready for evaluation by the IBM and SRM University-AP academic review panel.
