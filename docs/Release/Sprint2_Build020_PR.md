## Summary

Adds controlled approval records for Sprint archive retention plans.

## Changes

- Binds approval to the exact retention-plan SHA-256.
- Requires reviewer identity and rationale.
- Records approved action types and decision count.
- Detects retention-plan changes after approval.
- Does not execute any retention action.
- Adds an approval CLI, tests, ES-016, and an operational runbook.
- Makes no change to pre-existing legacy Pass1 files.

## Verification

- Full test suite passes.
- Ruff passes.
- Coverage remains at or above 80%.
- Legacy preservation tests pass.

## Merge target

`feature/sprint2-build020` → `develop`
