# Build064 — Twice-Daily Scheduler and Run Monitoring

Build064 installs auditable Windows Scheduled Tasks for the NRHIS morning and evening operations cycles. The default schedule is 7:00 AM and 6:00 PM Central time. Scheduled executions remain pre-QA by default (`QaPassesCompleted = 0`), so automation cannot bypass the mandatory two-pass verification and post-generation visual QA release controls.

## Commands

```powershell
.\scripts\Install-NrhisOperationsSchedule.ps1 -Replace
.\scripts\Get-NrhisOperationsScheduleStatus.ps1
.\scripts\Remove-NrhisOperationsSchedule.ps1
```

Each run writes a timestamped log under `data\nrhis\scheduler_logs` and a latest-slot receipt containing status, exit code, QA count, cycle name, and log path.
