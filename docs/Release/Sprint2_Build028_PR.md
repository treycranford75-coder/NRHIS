## Summary

Moves operator handoff files outside the repository and hardens manual release
clipboard sequencing.

## Changes

- Stores handoff files under local application data.
- Prevents generated handoff files from dirtying the Git working tree.
- Updates the handoff copy helper to use the external location.
- Adds a dedicated manual-release helper.
- Opens the release page before copying Markdown notes.
- Prints clear manual-release instructions after copying.
- Adds tests, ES-024, and an operational runbook.
- Makes no change to pre-existing legacy Pass1 files.

## Verification

- Full test suite passes.
- Ruff passes.
- Coverage remains at or above 80%.
- Legacy preservation tests pass.
- External handoff storage and clipboard sequencing are tested.

## Merge target

`feature/sprint2-build028` -> `develop`
