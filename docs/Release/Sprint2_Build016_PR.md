## Summary

Adds the machine-readable Sprint 2 closeout manifest and release-inventory gate.

## Changes

- Defines release inventory records for build, tag, commit, title, tests, and coverage.
- Verifies uninterrupted build-number continuity.
- Requires unique tags and merge commits.
- Enforces the configured coverage floor.
- Requires positive test evidence and pre-release classification.
- Writes deterministic Sprint closeout JSON.
- Adds a closeout CLI, tests, ES-012, and an operational runbook.
- Makes no change to pre-existing legacy Pass1 files.

## Verification

- Full test suite passes.
- Ruff passes.
- Coverage remains at or above 80%.
- Legacy preservation tests pass.
- Continuity, coverage failure, JSON loading, report export, and CLI behavior are tested.

## Merge target

`feature/sprint2-build016` → `develop`
