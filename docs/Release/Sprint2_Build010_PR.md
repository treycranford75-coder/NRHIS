## Summary

Adds controlled approval and revocation for calibration reference cases.

## Changes

- Separates Build009 capture from approval.
- Validates all artifacts before approval.
- Requires reviewer identity and rationale.
- Creates immutable approval records.
- Supports controlled revocation without deleting approval history.
- Adds an approval CLI, tests, ES-006, and an operational runbook.
- Makes no change to pre-existing legacy Pass1 files.

## Verification

- Full test suite passes.
- Ruff passes.
- Coverage remains at or above 80%.
- Legacy preservation tests pass.
- Approval, duplicate approval, hash mismatch, revocation, and CLI behavior are tested.

## Merge target

`feature/sprint2-build010` → `develop`
