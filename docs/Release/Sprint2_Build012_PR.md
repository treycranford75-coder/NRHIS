## Summary

Adds controlled comparison of candidate calibration artifacts against approved reference cases.

## Changes

- Requires approved reference cases by default.
- Compares JSON using structural and ignored-key controls.
- Compares CSV using stable keys and numeric tolerances.
- Compares other artifacts by exact bytes.
- Reports missing candidate artifacts and detailed differences.
- Exports deterministic JSON comparison reports.
- Adds a comparison CLI, tests, ES-008, and an operational runbook.
- Makes no change to pre-existing legacy Pass1 files.

## Verification

- Full test suite passes.
- Ruff passes.
- Coverage remains at or above 80%.
- Legacy preservation tests pass.
- Matching, difference, missing artifact, approval enforcement, JSON export, and CLI behavior are tested.

## Merge target

`feature/sprint2-build012` → `develop`
