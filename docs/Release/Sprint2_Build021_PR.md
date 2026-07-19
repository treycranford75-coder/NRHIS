## Summary

Adds controlled archive-retention action manifests.

## Changes

- Binds actions to the exact approved plan and approval hashes.
- Generates dry-run action manifests by default.
- Records action count, archive IDs, requested actions, and reasons.
- Detects plan, approval, and action-count changes.
- Performs no archive deletion, movement, or quarantine.
- Adds an action-manifest CLI, tests, ES-017, and an operational runbook.
- Makes no change to pre-existing legacy Pass1 files.

## Verification

- Full test suite passes.
- Ruff passes.
- Coverage remains at or above 80%.
- Legacy preservation tests pass.
- Creation, validation, hash binding, count validation, and CLI behavior are tested.

## Merge target

`feature/sprint2-build021` → `develop`
