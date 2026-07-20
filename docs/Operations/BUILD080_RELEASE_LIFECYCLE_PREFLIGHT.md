# Build080 Release Lifecycle Preflight

Build080 adds a deterministic preflight command for the NRHIS release lifecycle.

Run before a build:

```powershell
.\scripts\release\Test-NrhisReleaseLifecycle.ps1 -RequireGitHubAuthentication
```

The command verifies required release scripts, PowerShell syntax, GitHub CLI availability, optional authentication, idempotent branch cleanup contracts, and the verified completion-receipt contract required by installer archival.

A machine-readable receipt is written to `data/nrhis/release/lifecycle-preflight.json`.
