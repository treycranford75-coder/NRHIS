# Sprint 2 Build003 Release Checklist

## Scope

Reproducible developer environment and validation workflow.

## Acceptance criteria

- [ ] `docs/Development/DEV_SETUP.md` is present.
- [ ] `scripts/Verify-Environment.ps1` is present.
- [ ] The script checks Git and Python availability.
- [ ] The script enforces Python 3.11 or later.
- [ ] The script verifies editable NRHIS imports.
- [ ] Runtime and development dependencies are verified.
- [ ] Ruff and pytest run successfully.
- [ ] Environment-contract tests pass.
- [ ] `CONTRIBUTING.md` includes the approved quick-start section.
- [ ] No file under `src/nrhis_calibration/legacy` is modified.
- [ ] GitHub Actions passes.
- [ ] Pull request targets `develop`.
- [ ] Release candidate is tagged only after merge validation.
