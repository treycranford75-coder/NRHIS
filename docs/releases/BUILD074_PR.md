# Build074: add resumable and idempotent release lifecycle

## Summary
- Adds `Resume-NrhisBuildLifecycle.ps1`.
- Detects already-merged pull requests before attempting merge.
- Skips duplicate completion when a completion receipt exists.
- Skips duplicate archival when an archive manifest exists.
- Prints an exact recovery command whenever lifecycle execution is blocked.
- Retains Build073 CI-watch, merge, completion, archival, and next-build contracts.

## Validation
- Deterministic Build074 lifecycle tests.
- Historical Build073 lifecycle behavior retained.
