# Production Release Gate

The repository has one canonical end-to-end release command:

```bash
python scripts/release_gate.py --strict-git
```

The production gate is independent of contest, challenge-kit, mock-harness or external-benchmark validation. It verifies only internal software contracts and reproducibility.

The gate performs:

1. security scanning;
2. Ruff static analysis;
3. Python compilation;
4. deterministic notebook regeneration and verification;
5. test collection and strict test execution;
6. deterministic benchmark regeneration;
7. generated-artifact checks;
8. internal repository contract validation;
9. dependency vulnerability auditing;
10. clean-worktree reproducibility checks;
11. wheel and source-distribution builds;
12. isolated installed-wheel smoke testing;
13. final clean-worktree verification.

CI runs the same gate with the pinned runtime/test dependency set.

The tested production runtime is Python 3.11.17. Package metadata intentionally declares Python 3.11 only so the release contract matches the verified runtime.
