# QFF 2026 Phase 1 — Engineering Readiness Matrix

| Area | Status | Evidence |
|---|---|---|
| Exactly one problem statement | PASS | S3 is the only selected problem statement. |
| Phase 1 scope | PASS | Processor C / custom Processor D work is excluded. |
| Notebook | PASS | 23-section notebook is generated deterministically and syntax-verified. |
| Reusable implementation | PASS | Validated processors, routing, metrics, Bell benchmark and Trotter demonstrator are present. |
| Input validation | PASS | Numeric, probability, topology, statevector and trajectory guards are implemented. |
| Resource-exhaustion protection | PASS | Statevector memory and trajectory-count guards are enforced. |
| Routing correctness | PASS | Shortest-path routing is derived from the coupling graph instead of hardcoded topology assumptions. |
| Noise/readout model consistency | PASS | Practice Bell benchmark applies gate-error and readout-error channels explicitly. |
| Statistical handling | PASS | Practice Trotter benchmark uses online mean/variance accumulation. |
| Tests | PASS | Validation, routing, normalization, determinism, zero-noise and readout paths are covered. |
| CI | PASS | Dependency checks, compile checks, notebook verification, tests, benchmarks, figures and repository validation run automatically. |
| Official S3 scientific inputs | BLOCKED | Organizer Challenge Kit is not present in the available repository materials. |
| Official Processor A | BLOCKED | Current local model is explicitly illustrative. |
| Official Processor B | BLOCKED | Current local model is explicitly illustrative and is not a substitute for the organizer definition. |
| Official S3 result table | BLOCKED | Must be regenerated from organizer-defined S3 inputs and official A/B definitions. |
| Official submission readiness | BLOCKED | Validation intentionally fails closed until the official Challenge Kit is integrated. |

## Readiness verdict

**GREEN for the engineering scaffold and practice benchmark. RED for official scientific submission until the organizer-provided S3 Challenge Kit is integrated.**

The official gate is deliberately conservative: it is better to reject an incomplete official submission than to represent illustrative values as organizer-certified results.
