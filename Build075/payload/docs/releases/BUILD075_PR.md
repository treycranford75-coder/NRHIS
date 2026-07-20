# Build075: make release branch cleanup idempotent

## Summary

- Check for the local feature branch before `git branch -D`.
- Check for the remote feature branch before `git push origin --delete`.
- Treat an already-absent branch as successful cleanup.
- Preserve terminating failures for genuine Git inspection or deletion errors.
- Keep the resumable Build074 lifecycle and all historical release contracts intact.

## Verification

- Deterministic Build075 branch-cleanup tests.
- Existing release lifecycle tests remain applicable.
