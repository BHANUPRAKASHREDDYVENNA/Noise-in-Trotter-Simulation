# Official SRM University-AP QFF 2026 Environment Specification & Validation

> **Event:** IBM Partner Plus · SRM University-AP Qiskit Fall Fest 2026 Hackathon  
> **Official Setup Guide:** `QFF_2026_Setup_Guide_Windows.pdf` ("Laptop Setup (Windows)")  
> **Official Setup Script:** `QFF_2026_INSTALL_AND_TEST_WINDOWS.ps1`  
> **Official Test Report:** `C:\QFF\QFF2026_TEST_REPORT.txt`  
> **Target Track:** Track 3: Quantum Simulation (Hamiltonian Dynamics)  
> **Problem Statement:** PS-S3: Noise Accumulation in Trotter Circuits  
> **Verification Status:** **100% PASS (110/110 Project Tests Passing in Official Venv)**

---

## 1. Official Host System & Environment Configuration

The hackathon host environment was provisioned and validated according to the official organizers' specification:

| Parameter | Specification | Host System Status |
| :--- | :--- | :--- |
| **Operating System** | Windows 10/11 (64-bit) | Microsoft Windows 11 Home Single Language (build 26300) |
| **Processor Architecture**| AMD64 | AMD64 (15.6 GB RAM) |
| **PowerShell** | PowerShell 5.1+ Desktop | PowerShell 5.1.26100.9711 |
| **Base Python** | Python 3.11.9 (AMD64) | `C:\Users\venna\AppData\Local\Programs\Python\Python311\python.exe` |
| **Official Virtual Environment** | Dedicated Hackathon Venv | `C:\QFF\.qff2026-venv` |
| **Registered Jupyter Kernel** | `qff2026` | Display Name: `Python (QFF 2026)` |
| **Official JupyterLab Executable**| Standalone Browser UI | `C:\QFF\.qff2026-venv\Scripts\jupyter-lab.exe` |

---

## 2. Key Package Versions in Official Environment

The official QFF 2026 environment (`C:\QFF\.qff2026-venv`) provides the unified scientific and quantum software stack:

- **Core Quantum Framework:** `qiskit==2.6.1`, `qiskit-aer==0.18.2`
- **Quantum Application Modules:**
  - `qiskit-algorithms==0.4.0`
  - `qiskit-ibm-runtime==0.51.0`
  - `qiskit-machine-learning==0.9.1`
  - `qiskit-mitigation==0.1.1`
  - `qiskit-nature==0.8.0`
  - `qiskit-optimization==0.7.0`
  - `qiskit-qasm3-import==0.6.0`
- **Alternative Frameworks:** `pennylane==0.45.1`, `qutip==5.3.1`
- **Scientific Foundation:** `numpy==2.4.6`, `scipy==1.17.1`, `pandas==3.1.0`, `matplotlib==3.11.2`, `networkx==3.6.1`, `sympy==1.14.0`, `scikit-learn==1.9.1`
- **Post-Quantum Cryptography:** `cryptography==50.0.2`, `pqcrypto==1.0.0`
- **Testing & Verification:** `pytest==9.2.0`

---

## 3. Official Functional Self-Test Results (`QFF2026_TEST_REPORT.txt`)

The official installer executed 33 functional self-tests across all competition tracks:
- **Result:** `ALL CHECKS PASSED (32 passed, 0 failed, 1 expected-fail)`
- *Note:* The single `EXPECTED-FAIL` is for `PySCFDriver` under Chemistry, which is normal on Windows due to lack of native Windows PySCF binaries.

Key track checks verified:
1. `Simulation: Aer Bell state`: **PASS** (`{'00': 501, '11': 499}`)
2. `Drawing: matplotlib`: **PASS** (`circuit drawn`)
3. `Algorithms: VQE`: **PASS** (`energy -1.118 (exact -1.118)`)
4. `Optimization: QAOA`: **PASS** (`solution [0.0, 1.0]`)
5. `QML: EstimatorQNN`: **PASS** (`output shape (1, 1)`)
6. `IBM Runtime: fake backend`: **PASS** (`shots complete`)

---

## 4. PS-S3 Verification in Official QFF Environment

Executing the PS-S3 project directly using the official hackathon binary (`C:\QFF\.qff2026-venv\Scripts\python.exe`):

### 4.1 Master Pytest Suite (Combined Phase 1 + Phase 2)
```powershell
cd C:\Users\venna\.gemini\antigravity\scratch\Noise-in-Trotter-Simulation
C:\QFF\.qff2026-venv\Scripts\python.exe -m pytest -q
```
**Output:**
```text
110 passed in 22.76s (100% pass rate)
```

### 4.2 Phase 1 & Phase 2 Submission Contract Validators
```powershell
C:\QFF\.qff2026-venv\Scripts\python.exe Phase1/scripts/validate_submission.py --practice
C:\QFF\.qff2026-venv\Scripts\python.exe Phase2/scripts/validate_submission.py --practice
```
**Output:**
```text
Repository validation: PASS
Repository validation: PASS
```

### 4.3 Official Processor D Design Rule Check
```powershell
cd Phase2
C:\QFF\.qff2026-venv\Scripts\python.exe check_processor_d.py processors/processor_D.json 4
```
**Output:**
```text
OK - Processor D satisfies all design rules.
```

---

## 5. Judge & Evaluator Reproduction Instructions

Organizers and judges evaluating this submission on the official SRM University-AP setup can reproduce all results immediately:

1. **Launch JupyterLab with Hackathon Environment:**
   ```powershell
   C:\QFF\.qff2026-venv\Scripts\jupyter-lab.exe
   ```
2. **Open Master Notebook:**
   Navigate to `Noise-in-Trotter-Simulation/Phase2/main.ipynb`.
3. **Confirm Kernel:**
   Select the **`Python (QFF 2026)`** kernel from the dropdown menu (or click "Kernel -> Change Kernel -> Python (QFF 2026)").
4. **Run Full Notebook:**
   Click "Run -> Run All Cells". All 23 sections, Trotter scans, high-resolution plots, and statistical metrics execute cleanly without warnings or missing dependencies.
