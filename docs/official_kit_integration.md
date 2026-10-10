# S3 Official Challenge Kit Integration

This file is the controlled handoff point between the runnable S3 practice scaffold and the final Phase-1 competition benchmark.

## What is already complete

The repository has the Phase-1 architecture workflow, notebook, reusable source modules, tests, practice benchmarks, figures, reporting, AI disclosure and passing CI. The practice workflow deliberately avoids claiming organizer-certified S3 numbers.

## What is still kit-dependent

The official Phase-1 instructions say the selected Problem Statement's Challenge Kit determines the problem-specific inputs/instances, required outputs, Processor A/B definitions and other benchmark fields. Do not replace these with assumptions.

Before an official run, obtain these exact items:

1. Organizer-supplied S3 problem instance / Hamiltonian / input definition.
2. Exact Processor A definition.
3. Exact Processor B definition.
4. Required S3 output variables and metric definitions.
5. Any organizer-specified reference/classical baseline.
6. The kit version or release identifier.

## Controlled integration procedure

1. Copy the organizer-provided files into data/official_kit/ without modifying the source copies.
2. Create data/official_kit/manifest.json from the provided template and record the kit version plus relative paths to the instance and Processor A/B definitions.
3. Replace the illustrative processors/processor_A.json and processors/processor_B.json with normalized copies of the official definitions. Each must include source=official_challenge_kit.
4. Change data/guide_settings.json status to OFFICIAL_CHALLENGE_KIT and replace only the settings explicitly defined by the kit.
5. Update the S3-specific workload code so the official input drives the same logical workload on A and B.
6. Use src/routing.py with the official coupling maps and record depth, 2Q gates, SWAP/routing overhead, physical qubits and the required S3 problem metric.
7. Regenerate machine-readable outputs and figures from the official benchmark only.
8. Update report/report.md with the measured A/B comparison and evidence-based explanation.
9. Run:

```bash
python scripts/validate_submission.py --practice
pytest -q
python scripts/run_bell_benchmark.py
python scripts/run_practice.py
python scripts/validate_submission.py --official
```

10. Re-open the notebook from a clean environment and run it top-to-bottom before submission.

## Safety rule

Never delete or overwrite the original kit source files merely to make the validator pass. The validator is intended to catch accidental promotion of illustrative data into an official submission.