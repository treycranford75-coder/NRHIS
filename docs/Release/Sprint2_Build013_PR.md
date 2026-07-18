## Summary

Adds controlled dual-run calibration verification.

## Changes

- Executes calibration through the Build006 public API.
- Requires a successful calibration run before comparison.
- Compares generated artifacts through the Build012 controls.
- Requires approved reference cases by default.
- Writes deterministic comparison and dual-run summary reports.
- Returns a nonzero status when artifacts differ.
- Adds a dual-run CLI, tests, ES-009, and an operational runbook.
- Makes no change to pre-existing legacy Pass1 files.

## Verification

- Full test suite passes.
- Ruff passes.
- Coverage remains at or above 80%.
- Legacy preservation tests pass.
- Successful run, failed run, mismatch summary, and CLI behavior are tested.

## Merge target

`feature/sprint2-build013` → `develop`
