# Build066 — Scheduler Health Monitoring

Build066 adds a machine-readable health check for the two NRHIS Windows Scheduled Tasks and the latest scheduled operations-cycle evidence.

## Checks

- Morning and evening tasks exist.
- Each task is in Ready or Running state.
- The latest operations cycle exists and completed.
- The latest scheduler receipt exists and reports exit code 0.

## Run

```powershell
.\scripts\Test-NrhisSchedulerHealth.ps1
```

Use `-FailOnUnhealthy` for monitoring or CI workflows that must return a nonzero exit code when the scheduler is unhealthy.
