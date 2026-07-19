## Summary

Adds immutable calibration release-evidence bundles.

## Changes

- Copies controlled evidence artifacts into immutable bundle directories.
- Writes deterministic evidence manifests.
- Records SHA-256 digests and byte sizes.
- Rejects missing sources, duplicate filenames, and duplicate bundle IDs.
- Detects artifact tampering during validation.
- Adds an evidence CLI, tests, ES-010, and an operational runbook.
- Makes no change to pre-existing legacy Pass1 files.

## Verification

- Full test suite passes.
- Ruff passes.
- Coverage remains at or above 80%.
- Legacy preservation tests pass.
- Creation, validation, overwrite protection, missing files, duplicate names, and tamper detection are tested.

## Merge target

`feature/sprint2-build014` → `develop`
