# Production Release Gate

The repository has one canonical end-to-end release command:

```bash
python scripts/release_gate.py --strict-git
```

The gate performs:

1. repository security audit;
2. Ruff static analysis;
3. Python compilation;
4. deterministic notebook regeneration and verification;
5. test collection and strict test execution;
6. S3 practice benchmark regeneration;
7. figure regeneration;
8. repository validation;
9. dependency vulnerability scanning with pip-audit;
10. reproducibility checks against committed generated artifacts;
11. wheel and source-distribution builds;
12. installed-wheel import smoke testing;
13. final clean-worktree verification.

CI runs the same gate with the pinned runtime/test dependency set.

The supported production Python runtime is Python 3.11.17. The package metadata intentionally declares Python 3.11 only so that the release contract matches the tested runtime instead of advertising unverified interpreter versions.
