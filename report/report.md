# S3 Phase 1 — Scientific Report

## 1. Problem statement

**S3 — Noise in Trotter Simulation** is the selected problem statement for the project.

## 2. Scope

Only the online Phase-1 A/B architecture study is included.

## 3. Method

Problem/algorithm → logical circuit → placement/routing/gate decomposition → physical processor → measurement → problem + architecture metrics.

## 4. Architecture experiment

A Bell-state preparation is used because the guide explicitly presents it as an interpretable coherence benchmark. The benchmark reports XX, YY and ZZ correlations and quantifies fidelity, routing overhead and postselection yield.

## 5. Processor comparison — practice models only

The current local practice comparison uses an illustrative fully connected five-qubit graph for A and an illustrative five-qubit line graph for B. These are **not** the official Processor A/B definitions: the supplied geometry-aware presentation describes A as 5 qubits and B as 7 qubits with a heavy-hex-inspired graph. The official S3 Challenge Kit must supply the exact definitions before any result can be treated as the competition A/B benchmark. The same logical workload is used in this practice experiment, but the model differences are illustrative rather than organizer-certified.

## 6. Routing analysis

The line topology requires routing for long-range interactions. The resulting extra two-qubit operations are recorded as depth and routing/SWAP overhead.

## 7. Noise analysis

The project applies an illustrative depolarizing proxy to show how additional two-qubit work can reduce observed quality. The guide's pedagogical noise examples are treated as a modeling demonstration rather than hardware characterization.

## 8. Protection / postselection

The benchmark reports accepted versus discarded computational-basis shots and the resulting postselection yield.

## 9. Limitations

The supplied general participant instructions say the selected problem's Challenge Kit determines problem-specific instances, outputs, and platform definitions. The complete official S3 kit and its exact processor definitions are not yet verified in this repository. The numerical Trotter settings, processor graphs, noise rates, and benchmark outputs are therefore illustrative practice values and must not be presented as organizer-certified values or official S3 results.

## 10. Reproducibility

Random seeds, shot/trajectory counts and processor JSON settings are recorded. Figures are regenerated from saved result files.

## 11. Conclusions

The project demonstrates the central Phase-1 principle: the same logical quantum solution can acquire different physical costs under different coupling graphs, and those architecture-induced differences can alter the observed quality of a noisy execution.

## 12. Submission-readiness gate

The current repository is practice-complete but kit-blocked. Continuous integration is green and the reproducible practice workflow, notebook structure, tests, metrics, figures and reporting scaffold are in place. The only remaining scientific substitution is the organizer-defined S3 Challenge Kit: its S3 instance, required outputs and exact Processor A/B definitions must replace the illustrative files before final competition results are generated.

The official readiness validator is intentionally strict and will refuse to declare the repository submission-ready while any referenced processor/model remains illustrative or while the official kit manifest is missing. This prevents a false PASS.

## 12. Engineering hardening and verification

The implementation was hardened around input validation, numerical resource limits, routing correctness, readout modeling, statistical accumulation, notebook reproducibility, CI artifact generation and fail-closed official validation.

The practice benchmark is therefore a reproducible engineering scaffold. It remains explicitly separate from official competition results until the organizer Challenge Kit is applied.
