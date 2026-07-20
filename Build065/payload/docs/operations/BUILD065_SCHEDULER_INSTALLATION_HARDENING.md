# Build065 Scheduler Installation Hardening

Build065 hardens the Windows Task Scheduler installer proven during Build064 field installation.

## Controls

- Refuses installation unless the PowerShell process is elevated.
- Uses `-ErrorAction Stop` for task registration.
- Prints success only after the task can be read back from Task Scheduler.
- Verifies every enabled schedule slot after registration.
- Retains process-scoped `-ExecutionPolicy Bypass` for scheduled child runs.
- Leaves the publication QA count at zero by default.
