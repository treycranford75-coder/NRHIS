# Sprint 2 Build002 Release Checklist

## Scope

Repository audit and legacy Pass1 preservation baseline.

## Acceptance criteria

- [ ] `DEVELOPMENT_PLAN.md` is present at the repository root.
- [ ] Repository audit is complete.
- [ ] Legacy Pass1 files remain in their original location.
- [ ] No pre-existing legacy Pass1 file was intentionally modified.
- [ ] SHA-256 preservation manifest is present.
- [ ] Automated tests validate all manifested files.
- [ ] Automated tests reject unmanifested additions.
- [ ] Full test suite passes.
- [ ] Ruff passes.
- [ ] GitHub Actions passes.
- [ ] Pull request targets `develop`.
- [ ] Release candidate is tagged only after merge validation.

## Validation baseline

- Expected tests: 10
- Required lint result: all checks passed
- Required CI status: green
