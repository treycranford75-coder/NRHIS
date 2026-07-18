## Summary

Adds immutable Sprint 2 closeout archives.

## Changes

- Archives the accepted release inventory and closeout report.
- Requires an accepted closeout report before archive creation.
- Writes a deterministic Sprint archive manifest.
- Records SHA-256 digests and byte sizes.
- Refuses archive overwrite.
- Detects archived-artifact tampering.
- Adds an archive CLI, tests, ES-013, and an operational runbook.
- Makes no change to pre-existing legacy Pass1 files.

## Verification

- Full test suite passes.
- Ruff passes.
- Coverage remains at or above 80%.
- Legacy preservation tests pass.
- Creation, acceptance enforcement, overwrite protection, tamper detection, and CLI behavior are tested.

## Merge target

`feature/sprint2-build017` -> `develop`
