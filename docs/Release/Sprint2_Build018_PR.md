## Summary

Adds discovery and indexing for immutable Sprint archives.

## Changes

- Recursively discovers Sprint archive manifests.
- Validates each archive through ES-013.
- Keeps invalid archives visible with validation errors.
- Filters by validation status and Sprint metadata.
- Exports deterministic Sprint archive index JSON.
- Adds an archive-index CLI, tests, ES-014, and an operational runbook.
- Makes no change to pre-existing legacy Pass1 files.

## Verification

- Full test suite passes.
- Ruff passes.
- Coverage remains at or above 80%.
- Legacy preservation tests pass.
- Discovery, invalid archive handling, filtering, export, and CLI behavior are tested.

## Merge target

`feature/sprint2-build018` → `develop`
