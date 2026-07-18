## Summary

Adds non-destructive retention planning for immutable Sprint archives.

## Changes

- Classifies indexed archives as retain, review, or quarantine.
- Retains the configured number of latest valid archives.
- Marks older valid archives for review.
- Marks invalid archives for quarantine.
- Leaves all archives unchanged.
- Writes deterministic retention-plan JSON.
- Adds a retention CLI, tests, ES-015, and an operational runbook.
- Makes no change to pre-existing legacy Pass1 files.

## Verification

- Full test suite passes.
- Ruff passes.
- Coverage remains at or above 80%.
- Legacy preservation tests pass.
- Classification, invalid limits, JSON export, reload, and CLI behavior are tested.

## Merge target

`feature/sprint2-build019` → `develop`
