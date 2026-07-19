# Sprint 2 Build004 Release Checklist

## Scope

Test coverage and automated quality baseline.

## Acceptance criteria

- [ ] `coverage` is included in development dependencies.
- [ ] `pytest-cov` is included in development dependencies.
- [ ] Branch coverage is enabled.
- [ ] `src/nrhis_calibration/legacy/*` is excluded.
- [ ] Coverage floor is 80%.
- [ ] Terminal missing-line reporting is enabled.
- [ ] `coverage.xml` is generated.
- [ ] GitHub Actions uploads the XML artifact.
- [ ] Coverage-contract tests pass.
- [ ] Full test suite passes.
- [ ] Ruff passes.
- [ ] No file under `src/nrhis_calibration/legacy` is modified.
- [ ] Pull request targets `develop`.
- [ ] Release candidate is tagged only after merge validation.
