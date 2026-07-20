# Build080: add release lifecycle preflight gate

## Summary
- Adds `Test-NrhisReleaseLifecycle.ps1`.
- Validates required release helpers and PowerShell syntax.
- Verifies completion, archive, and idempotent branch-cleanup contracts.
- Writes `data/nrhis/release/lifecycle-preflight.json`.
- Adds deterministic Build080 regression tests.
