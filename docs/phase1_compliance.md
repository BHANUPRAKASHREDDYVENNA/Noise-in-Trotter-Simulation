# Phase 1 Compliance Boundary

This repository is intentionally separated into two categories:

1. Phase-1 common benchmark: S3 — Noise in Trotter Simulation, run with the same controlled workload on Processor A and Processor B.
2. Auxiliary engineering material: educational Bell/protection code retained for offline-study support and unit testing.

The supplied competition materials state that the online phase compares Processor A and Processor B using solution quality, circuit cost, routing/SWAP overhead, physical-qubit use and noise/reproducibility measurements. The Bell-correlation and protection challenge is reserved for the offline Processor C/D stage. This repository therefore does not use Bell outputs as the Phase-1 common benchmark.

## Enforcement

- S3 is the only selected problem statement.
- Processor C and custom Processor D work are excluded from the Phase-1 implementation.
- Practice Processor A/B models are explicitly illustrative until the organizer Challenge Kit is integrated.
- Bell outputs, where generated, are stored under results/auxiliary/ and are not used as the official A/B comparison table.
- The official validator fails closed until the organizer-supplied S3 Challenge Kit is present and the official Processor A/B definitions replace the illustrative models.
- Generated practice results are checked in CI for reproducibility.

## Submission boundary

Do not submit practice numerical values as organizer-certified results. The official Challenge Kit must provide the selected S3 instance, exact Processor A/B definitions, required outputs, and related benchmark fields before official result generation.
