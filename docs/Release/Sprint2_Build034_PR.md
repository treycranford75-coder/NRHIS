## Summary

Adds a post-publication verification handoff for manual releases and automatic
verification after authenticated GitHub CLI publication.

## Changes

- Generates an exact bounded release-verification command.
- Copies the verification command to the clipboard.
- Writes an external post-publication verification handoff.
- Records the expected release-evidence location.
- Preserves browser-first manual publication.
- Automatically verifies releases published through GitHub CLI.
- Reports success only after authenticated publication is publicly verified.
- Adds tests, ES-030, and an operational runbook.
- Makes no change to pre-existing legacy Pass1 files.

## Verification

- PowerShell syntax validation passes.
- Payload consistency verification passes.
- Full test suite passes.
- Ruff passes.
- Coverage remains at or above 80%.
- Legacy preservation tests pass.
- Manual handoff and authenticated post-publication verification are tested.

## Merge target

`feature/sprint2-build034` -> `develop`
