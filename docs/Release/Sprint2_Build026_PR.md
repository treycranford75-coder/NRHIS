## Summary

Adds a permanent generic build bootstrap and automatic cleanup of temporary
starter scripts.

## Changes

- Adds a generic one-command build starter.
- Locates one-step ZIPs in common download locations.
- Extracts and verifies the build automatically.
- Removes stale extraction folders.
- Removes temporary starter scripts during release completion.
- URL-encodes manual release tags and titles.
- Adds tests, ES-022, and an operational runbook.
- Makes no change to pre-existing legacy Pass1 files.

## Verification

- Full test suite passes.
- Ruff passes.
- Coverage remains at or above 80%.
- Legacy preservation tests pass.
- Bootstrap discovery, extraction, cleanup, and release URL handling are tested.

## Merge target

`feature/sprint2-build026` -> `develop`
