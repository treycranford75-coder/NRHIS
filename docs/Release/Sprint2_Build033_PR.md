## Summary

Adds payload-consistency verification and complete automatic staging for every
required build file.

## Changes

- Compares extracted payload files with installed working-tree files using SHA-256.
- Blocks reruns when the working tree and payload source differ.
- Requires corrections to be made in the payload source.
- Adds a reusable complete-staging helper.
- Automatically stages every discovered payload file.
- Ensures `scripts/release/Start-NrhisBuild.ps1` is automatically staged.
- Supports explicit additional and required files.
- Runs change-set completeness verification after staging.
- Adds tests, ES-029, and an operational runbook.
- Makes no change to pre-existing legacy Pass1 files.

## Verification

- PowerShell syntax validation passes.
- Payload consistency verification passes.
- Full test suite passes.
- Ruff passes.
- Coverage remains at or above 80%.
- Legacy preservation tests pass.
- Complete staging and SHA-256 payload comparison are tested.

## Merge target

`feature/sprint2-build033` -> `develop`
