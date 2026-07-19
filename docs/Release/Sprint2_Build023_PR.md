## Summary

Adds reusable automation for NRHIS validation, pull-request creation, and
post-merge release completion.

## Changes

- Adds a reusable release-validation script.
- Adds GitHub CLI pull-request creation with browser fallback.
- Adds post-merge validation, cleanup, tag verification, and release publishing.
- Preserves manual pull-request merging as the required release gate.
- Adds tests, ES-019, and an operational runbook.
- Makes no change to pre-existing legacy Pass1 files.

## Verification

- Full test suite passes.
- Ruff passes.
- Coverage remains at or above 80%.
- Legacy preservation tests pass.
- Automation safeguards and required release commands are tested.

## Merge target

`feature/sprint2-build023` -> `develop`
