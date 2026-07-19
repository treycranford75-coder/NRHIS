## Summary

Establishes the reproducible NRHIS Windows developer environment and local validation workflow.

## Changes

- Adds the Build003 developer setup guide.
- Adds `scripts/Verify-Environment.ps1`.
- Verifies Python, Git, editable NRHIS imports, runtime dependencies, development dependencies, Ruff, and pytest.
- Adds automated tests for the declared environment contract.
- Adds a reviewed appendix for expanding `CONTRIBUTING.md`.
- Adds the Build003 release checklist.
- Makes no changes under `src/nrhis_calibration/legacy`.

## Verification

- Environment contract tests pass.
- Full test suite passes.
- Ruff passes.
- `git diff --check` passes.
- `Verify-Environment.ps1` completes successfully.

## Merge target

`feature/sprint2-build003` → `develop`
