## Summary

Establishes the NRHIS branch-coverage baseline and CI regression gate.

## Changes

- Adds `coverage` and `pytest-cov` development dependencies.
- Configures branch coverage in `pyproject.toml`.
- Excludes the preservation-controlled legacy Pass1 tree.
- Establishes an 80% minimum coverage floor against an 82% measured baseline.
- Updates GitHub Actions to generate terminal and XML coverage reports.
- Uploads `coverage.xml` as a workflow artifact.
- Adds automated coverage-contract tests.
- Adds the Build004 coverage baseline document and release checklist.

## Verification

- Existing Build003 baseline: 13 tests passed.
- Measured branch coverage: 82%.
- Required regression floor: 80%.
- Ruff passes.
- Coverage XML is produced.
- No legacy Pass1 file is modified.

## Merge target

`feature/sprint2-build004` → `develop`
