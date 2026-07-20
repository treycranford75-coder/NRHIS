## Summary

Build089 stabilizes the NRHIS one-step release process after the Build088 repair cycle.

## Changes

- Uses `develop` as the controlling base branch.
- Performs a clean-tree gate before payload installation.
- Stages only an explicit Build089 allowlist.
- Rejects generated runtime data and oversized Git blobs.
- Runs Ruff and the full repository test suite with visible output.
- Uses noninteractive commits and automatic PR creation or reopening.
- Handles pending or temporarily absent CI checks.
- Merges, publishes the prerelease, writes receipts, cleans the feature branch, and creates the verified installer ZIP and checksum.

## Validation

Build089 must pass deterministic package tests, Ruff, and the complete repository test suite before commit or push.
