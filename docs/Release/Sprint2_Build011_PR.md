## Summary

Adds discovery, validation, filtering, and export for calibration reference cases.

## Changes

- Recursively discovers `case.json` manifests.
- Validates each case through the Build008 controls.
- Keeps invalid cases visible with validation errors.
- Filters by implementation, approval state, and validity.
- Exports deterministic JSON catalogs.
- Adds a catalog CLI, tests, ES-007, and an operational runbook.
- Makes no change to pre-existing legacy Pass1 files.

## Verification

- Full test suite passes.
- Ruff passes.
- Coverage remains at or above 80%.
- Legacy preservation tests pass.
- Discovery, invalid-case handling, filtering, JSON export, and CLI behavior are tested.

## Merge target

`feature/sprint2-build011` → `develop`
