NRHIS Sprint 2 Build064 — Twice-Daily Scheduler and Run Monitoring

1. Place this ZIP and its .sha256 file in C:\GitHub\NRHIS or Downloads.
2. From C:\GitHub\NRHIS run:
   .\scripts\release\Start-NrhisBuild.ps1 -BuildNumber "064"
3. After merge and completion, install the schedule with:
   .\scripts\Install-NrhisOperationsSchedule.ps1 -Replace
4. Inspect status with:
   .\scripts\Get-NrhisOperationsScheduleStatus.ps1

Scheduled runs default to zero QA passes and cannot authorize publication.
