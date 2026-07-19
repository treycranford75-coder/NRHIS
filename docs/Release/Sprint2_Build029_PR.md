## Summary

Adds dynamic payload-manifest staging, change-set completeness verification, and
a local CI-parity gate.

## Changes

- Builds the expected file list from the extracted payload.
- Supports explicit compatibility-test additions.
- Stages the complete expected change set automatically.
- Rejects missing expected files.
- Rejects unexpected staged repository files.
- Rejects unexpected untracked files.
- Adds a reusable CI-parity validation script.
- Mirrors Ruff, pytest, branch coverage, legacy preservation, and whitespace gates.
- Adds tests, ES-025, and an operational runbook.
- Makes no change to pre-existing legacy Pass1 files.

## Verification

- Full test suite passes.
- Ruff passes.
- Coverage remains at or above 80%.
- Legacy preservation tests pass.
- Dynamic payload manifest and change-set verification are tested.
- CI-parity commands are tested.

## Merge target

`feature/sprint2-build029` -> `develop`
