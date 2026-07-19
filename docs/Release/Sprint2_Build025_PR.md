## Summary

Adds release-environment preflight, explicit GitHub CLI bootstrap, and controlled
publication for existing release tags.

## Changes

- Adds repository, branch, cleanliness, Git, and Python preflight checks.
- Adds optional GitHub CLI installation through winget.
- Adds optional browser-based GitHub CLI authentication.
- Adds publication of a pre-release from an existing pushed tag.
- Rejects missing tags, unauthenticated GitHub CLI, and duplicate releases.
- Adds tests, ES-021, and an operational runbook.
- Makes no change to pre-existing legacy Pass1 files.

## Verification

- Full test suite passes.
- Ruff passes.
- Coverage remains at or above 80%.
- Legacy preservation tests pass.
- Preflight, explicit installation, authentication, tag verification, and
  duplicate-release safeguards are tested.

## Merge target

`feature/sprint2-build025` -> `develop`
