## Summary

Hardens the automated release workflow against wrong-base pull requests and
plain-text release-note publication.

## Changes

- Adds robust GitHub repository-slug parsing.
- Builds verified compare URLs from explicit base and head branches.
- Passes the repository explicitly to GitHub CLI commands.
- Copies release notes as raw Markdown during manual publication.
- Opens a release page prefilled with the correct tag and title.
- Adds a dedicated Markdown-copy helper.
- Adds tests, ES-020, and an operational runbook.
- Makes no change to pre-existing legacy Pass1 files.

## Verification

- Full test suite passes.
- Ruff passes.
- Coverage remains at or above 80%.
- Legacy preservation tests pass.
- Repository parsing, compare URL construction, and Markdown preservation are tested.

## Merge target

`feature/sprint2-build024` -> `develop`
