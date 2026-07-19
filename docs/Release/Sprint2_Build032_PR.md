## Summary

Hardens one-step build startup by installing bootstrap helpers before branch setup and guaranteeing the feature branch exists before commit.

## Changes

- Installs required bootstrap helpers before branch initialization.
- Adds a reusable build-branch initializer.
- Synchronizes `develop` without pruning.
- Creates the feature branch directly from the synchronized base branch.
- Prevents a commit on `develop` during the build workflow.
- Adds a reusable payload installer with bootstrap-file support.
- Preserves the permanent one-command starter.
- Adds tests, ES-028, and an operational runbook.
- Makes no change to pre-existing legacy Pass1 files.

## Verification

- PowerShell syntax validation passes.
- Full test suite passes.
- Ruff passes.
- Coverage remains at or above 80%.
- Legacy preservation tests pass.
- Bootstrap order, no-prune synchronization, branch creation, and payload installation are tested.

## Merge target

`feature/sprint2-build032` -> `develop`
