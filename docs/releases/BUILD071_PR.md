# Build071: automate pull-request creation in the one-step lifecycle

## NRHIS Sprint 2 — Build071

Build071 removes the recurring manual pull-request step from the NRHIS build lifecycle.

### Included

- Automatically creates a pull request after a successful build push
- Targets `develop` from `feature/sprint2-build###`
- Reuses an existing open pull request instead of creating duplicates
- Uses the build-specific PR title and Markdown body file
- Returns the PR URL to the operator
- Fails clearly when GitHub CLI is missing or unauthenticated
- Preserves checksum, extraction, entry-point, test, and child-process gates
- Provides `-SkipPullRequest` for deliberate offline diagnostics

### Expected lifecycle finish

```text
Build071 applied and pushed.
Pull request ready: https://github.com/.../pull/...
Waiting for CI and merge into develop.
```

Build070 remains complete, published, verified, and archived.
