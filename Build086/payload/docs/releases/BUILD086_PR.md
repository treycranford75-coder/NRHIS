# Build086: treat unregistered CI checks as pending

## Summary

- Retry the GitHub `no checks reported` state for up to two minutes.
- Record an expired registration window as pending, not failed.
- Preserve fail-fast blocking for genuine CI failures.
- Add deterministic lifecycle contract tests.
