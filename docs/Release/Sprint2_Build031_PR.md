## Summary

Commits the corrected published-release verifier, adds a PowerShell syntax gate,
and prevents interactive Git pruning during build synchronization.

## Changes

- Replaces the malformed release-verifier prerelease expression.
- Adds native PowerShell parser validation for release scripts.
- Runs the syntax gate before Python validation.
- Adds no-prune repository synchronization.
- Prevents stale remote-reference deletion prompts during builds.
- Updates release completion to use the no-prune synchronization helper.
- Adds tests, ES-027, and an operational runbook.
- Makes no change to pre-existing legacy Pass1 files.

## Verification

- PowerShell syntax validation passes.
- Full test suite passes.
- Ruff passes.
- Coverage remains at or above 80%.
- Legacy preservation tests pass.
- No-prune synchronization and parser-safe release verification are tested.

## Merge target

`feature/sprint2-build031` -> `develop`
