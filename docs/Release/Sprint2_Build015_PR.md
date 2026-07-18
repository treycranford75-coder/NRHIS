## Summary

Adds the final calibration release acceptance gate.

## Changes

- Validates the Build014 evidence bundle.
- Requires dual-run and comparison reports.
- Requires a successful comparison outcome by default.
- Produces deterministic release-gate JSON.
- Returns nonzero when any release check fails.
- Adds a release-gate CLI, tests, ES-011, and an operational runbook.
- Makes no change to pre-existing legacy Pass1 files.

## Verification

- Full test suite passes.
- Ruff passes.
- Coverage remains at or above 80%.
- Legacy preservation tests pass.
- Acceptance, mismatch rejection, missing artifact, JSON export, and CLI behavior are tested.

## Merge target

`feature/sprint2-build015` → `develop`
