NRHIS Sprint 2 Build065 - Scheduler Installation Hardening

1. Place this ZIP and its .sha256 file in a location searched by Start-NrhisBuild.ps1.
2. From C:\GitHub\NRHIS run:
   .\scripts\release\Start-NrhisBuild.ps1 -BuildNumber "065"
3. Review and merge the generated pull request into develop after CI passes.
4. Run .\Build065\Complete-Build065.ps1 after merge.
5. Install the schedule from an elevated PowerShell session:
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass -Force
   .\scripts\Install-NrhisOperationsSchedule.ps1 -Replace
