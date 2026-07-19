## Summary

Adds the controlled calibration reference-capture workflow.

## Changes

- Captures successful calibration run artifacts into immutable case directories.
- Writes capture records and Build008-compatible manifests.
- Hashes all captured artifacts.
- Rejects failed runs, missing artifacts, and duplicate case identifiers.
- Forces every captured case to remain unapproved.
- Adds a capture CLI, tests, ES-005, and an operational runbook.
- Makes no change to pre-existing legacy Pass1 files.

## Verification

- Full test suite passes.
- Ruff passes.
- Coverage remains at or above 80%.
- Legacy preservation tests pass.
- Capture, failure, missing-artifact, and no-overwrite behavior are tested.

## Merge target

`feature/sprint2-build009` → `develop`
