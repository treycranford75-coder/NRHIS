# Build074 — Resumable Release Lifecycle

Build074 adds a recovery command for interrupted or previously failed automated releases:

```powershell
.\scripts\release\Resume-NrhisBuildLifecycle.ps1 -BuildNumber "074"
```

The resume helper locates the build pull request, detects whether it is open or already merged, and continues only the unfinished steps. Completion and installer archival are guarded by their existing receipts so reruns do not duplicate release evidence.
