## Summary

Adds an isolated, additive compatibility wrapper for the preserved legacy Pass1 calibration implementation.

## Changes

- Adds `nrhis_calibration.compat`.
- Launches legacy Pass1 through a subprocess boundary.
- Captures stdout, stderr, timing, return code, metadata, and legacy script SHA-256.
- Adds a PowerShell operational entry point.
- Adds dry-run and timeout behavior.
- Adds tests, architecture documentation, and an operational runbook.
- Makes no functional change to pre-existing legacy Pass1 files.

## Verification

- Compatibility-wrapper tests pass.
- Full test suite passes.
- Ruff passes.
- Coverage remains above 80%.
- Legacy preservation tests pass.
- Dry-run smoke test passes.

## Merge target

`feature/sprint2-build005` → `develop`
