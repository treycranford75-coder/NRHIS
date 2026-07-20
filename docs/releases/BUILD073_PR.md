# Build073: automate CI, merge, completion, and archival

## Summary

Completes the NRHIS one-step lifecycle after pull-request creation.

## Included

- Watches required GitHub checks with fail-fast behavior.
- Blocks merge when CI fails.
- Automatically merges the successful PR into `develop`.
- Updates the local `develop` branch after merge.
- Runs `Complete-Build073.ps1` automatically.
- Archives installer artifacts automatically.
- Deletes the feature branch after merge.
- Preserves historical extraction reuse, `-ForceExtract`, and `-NoChain` contracts.
- Provides `-SkipLifecycle` and `-SkipArchive` diagnostic overrides.

## Validation

- Deterministic Build073 lifecycle tests.
- Historical release-workflow contracts retained.
