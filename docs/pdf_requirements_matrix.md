# QFF 2026 Phase 1 — Compliance and Readiness Matrix

This matrix distinguishes engineering readiness from requirements that depend on the organizer-provided S3 Challenge Kit.

| Requirement / area | Current status | Evidence / limitation |
|---|---|---|
| Exactly one problem statement | PASS | Repository declares S3 only. |
| Phase 1 only | PASS | No Processor C / custom Processor D execution is claimed. |
| Notebook, README, environment | PASS | Present and CI-verified. |
| Repository structure | PASS | Source, processors, results, tests, docs and report are separated. |
| S3 scientific instance | BLOCKED | The organizer-defined S3 instance is not present in the available materials. |
| Official Processor A | BLOCKED | Current local definition is explicitly illustrative. |
| Official Processor B | BLOCKED | Current local definition is explicitly illustrative. |
| Problem-specific official output schema | BLOCKED | Must come from the S3 Challenge Kit. |
| Practice Trotter demonstrator | PASS | Validated, reproducible and protected against unsafe resource requests. |
| Bell practice benchmark | PASS | Correlations, routing proxy, noise proxy and readout error are tested. |
| Routing/resource metrics | PASS | Depth, 2Q operations and routing overhead are calculated from validated topology. |
| A/B practice experiment | PASS | Same logical workload is run on both practice models. |
| Results and figures pipeline | PASS | Benchmarks and figure generation are executed in CI. |
| Tests and CI | PASS | Compile checks, notebook verification, unit tests and end-to-end practice artifacts are checked. |
| Official submission | BLOCKED | Official validation fails closed until the Challenge Kit is integrated. |

## Readiness verdict

Engineering scaffold: **READY**.

Official competition benchmark: **NOT READY until the organizer Challenge Kit is supplied and integrated**.
