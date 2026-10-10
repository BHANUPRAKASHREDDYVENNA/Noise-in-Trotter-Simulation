# QFF 2026 Phase 1 — Compliance and Readiness Matrix

This matrix distinguishes repository scaffolding from verified compliance with the organizer's selected-problem Challenge Kit.

| Requirement / area | Current status | Evidence / limitation | Next action |
|---|---|---|---|
| Exactly one problem statement | PASS (declared) | Repository declares S3 only. | Keep S3 as the only selected PS in all materials. |
| Phase 1 only | PASS (scope) | No Processor C / custom Processor D execution is claimed. | Keep all Phase 2 work out of scope. |
| Notebook, README, environment files | PRESENT | These files exist in the repository. | Re-run notebook top-to-bottom from a clean environment before submission. |
| S3-specific scientific instance | BLOCKED / NOT VERIFIED | General participant guide says the Challenge Kit determines problem-specific instances and required outputs; no complete S3 instance is confirmed in the current repository. | Obtain and use the official S3 Challenge Kit. |
| Official Processor A definition | BLOCKED / NOT VERIFIED | Current `processors/processor_A.json` is explicitly illustrative, not organizer-provided. | Replace with the exact kit definition. |
| Official Processor B definition | BLOCKED / NOT VERIFIED | Current `processors/processor_B.json` is explicitly illustrative, not organizer-provided. It does not match the 7-qubit heavy-hex-inspired B shown in the geometry-aware presentation. | Replace with the exact kit definition. |
| Required S3 algorithm / output schema | BLOCKED / NOT VERIFIED | Current Trotter settings are illustrative; required S3 outputs are not confirmed. | Follow the Challenge Kit without substituting a custom instance. |
| Practice Trotter demonstrator | PRESENT (illustrative only) | `src/practice_s3.py`, `data/practice_config.json`, and practice runner. | Keep practice outputs clearly separated from official results. |
| Bell-state practice benchmark | PRESENT (illustrative only) | `src/bell_benchmark.py` and `scripts/run_bell_benchmark.py` demonstrate correlations, routing/noise proxies and postselection. | Do not present this as the official S3 solution or an official A/B result. |
| Circuit depth / two-qubit gates / SWAPs / physical qubits | PARTIAL | Metric helpers exist, but official processor definitions and kit-specific measurements are not verified. | Recompute from official transpiled circuits and report required fields. |
| A/B experiment | PARTIAL (practice only) | Practice scripts compare local illustrative models. | Rerun identical official workload and settings on A and B. |
| Required result tables and graphs | PARTIAL | Practice CSVs and figures exist or can be regenerated. | Regenerate all outputs from the official benchmark and identify practice data clearly. |
| Tests and CI | IN PROGRESS | Unit tests and a CI workflow exist. CI is being strengthened to compile scripts and run the Bell practice script. | Confirm the branch workflow passes; then merge fixes. |
| Reproducibility | PARTIAL | Seeds and configuration are recorded for the practice models. | Pin a tested environment and document official kit version, commands and outputs. |
| Scientific interpretation | PARTIAL | Report explains practice topology/noise trade-offs. | Replace illustrative conclusions with measured official A/B evidence. |
| AI/LLM disclosure | PRESENT, VERIFY POLICY | README includes an AI-assisted development disclosure. | Confirm exact disclosure requirements with the event's official policy. |
| Public repository access | VERIFIED AT REPOSITORY LEVEL | Repository is public and user has push/admin permission. | Verify the final commit and judging access before submission. |

## Readiness verdict

**YELLOW — useful implementation scaffold, not yet a verified official S3 submission.**

The official Phase 1 instructions require the selected problem's Challenge Kit, matching A/B runs, required problem-specific metrics, reproducible results, and a structured repository. Until the S3 kit and its exact platform definitions are applied, the practice outputs must not be represented as official competition results.
