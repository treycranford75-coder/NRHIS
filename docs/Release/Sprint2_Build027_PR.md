## Summary

Adds a durable operator handoff for pull-request and release metadata.

## Changes

- Creates a build-specific operator handoff file.
- Records the PR base branch, compare branch, title, description, and URL.
- Records the release tag, title, and release notes.
- Copies the PR description to the clipboard automatically.
- Adds a helper to copy any handoff section on demand.
- Prints release title and tag during manual release fallback.
- Adds tests, ES-023, and an operational runbook.
- Makes no change to pre-existing legacy Pass1 files.

## Verification

- Full test suite passes.
- Ruff passes.
- Coverage remains at or above 80%.
- Legacy preservation tests pass.
- Handoff creation, clipboard behavior, compare URL, and section recovery are tested.

## Merge target

`feature/sprint2-build027` -> `develop`
