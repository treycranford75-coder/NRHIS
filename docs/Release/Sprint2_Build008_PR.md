## Summary

Adds controlled calibration reference-case manifests and validation.

## Changes

- Adds reference-case manifest data contracts.
- Adds manifest writer and loader.
- Adds SHA-256 validation for all listed artifacts.
- Adds explicit approved/unapproved state handling.
- Adds `--require-approved` enforcement.
- Adds a reference-case validation CLI.
- Adds tests, ES-004, and an operational runbook.
- Makes no change to pre-existing legacy Pass1 files.

## Verification

- Full test suite passes.
- Ruff passes.
- Coverage remains at or above 80%.
- Legacy preservation tests pass.
- Manifest hash mismatch and approval failures are tested.

## Merge target

`feature/sprint2-build008` → `develop`
