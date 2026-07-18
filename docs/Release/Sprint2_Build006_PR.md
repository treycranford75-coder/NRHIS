## Summary

Defines the stable NRHIS calibration API and controlled migration plan.

## Changes

- Adds implementation-neutral request and result contracts.
- Adds the `CalibrationRunner` protocol.
- Adds the `legacy-pass1` adapter and registry.
- Adds the `run_calibration()` public entry point.
- Exports the API from `nrhis_calibration`.
- Adds API tests and migration documentation.
- Makes no change to pre-existing legacy Pass1 files.

## Verification

- Full test suite passes.
- Ruff passes.
- Coverage remains at or above 80%.
- Legacy preservation tests pass.

## Merge target

`feature/sprint2-build006` → `develop`
