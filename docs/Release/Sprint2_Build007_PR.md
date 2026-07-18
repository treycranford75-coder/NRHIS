## Summary

Adds the calibration characterization harness and ES-003 comparison standard.

## Changes

- Adds SHA-256 reference-artifact hashing.
- Adds JSON structural and numeric-tolerance comparison.
- Adds CSV keyed-row comparison with numeric tolerances.
- Adds explicit difference records and reports.
- Adds synthetic contract fixtures and automated tests.
- Adds ES-003 and characterization architecture documentation.
- Makes no change to pre-existing legacy Pass1 files.

## Verification

- Full test suite passes.
- Ruff passes.
- Coverage remains at or above 80%.
- Legacy preservation tests pass.
- Synthetic reference fixtures pass characterization.

## Merge target

`feature/sprint2-build007` → `develop`
