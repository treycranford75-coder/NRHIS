## Summary

Adds public post-publication release verification and machine-readable release
evidence.

## Changes

- Verifies the published release through GitHub's public API.
- Confirms the exact tag and title.
- Confirms pre-release and non-draft status.
- Confirms exact Markdown release notes.
- Confirms a published release URL is present.
- Writes machine-readable verification evidence outside the repository.
- Adds bounded polling for newly published releases.
- Requires no GitHub CLI authentication for the public repository.
- Adds tests, ES-026, and an operational runbook.
- Makes no change to pre-existing legacy Pass1 files.

## Verification

- Full test suite passes.
- Ruff passes.
- Coverage remains at or above 80%.
- Legacy preservation tests pass.
- Public API retrieval, metadata checks, evidence output, and bounded polling are tested.

## Merge target

`feature/sprint2-build030` -> `develop`
