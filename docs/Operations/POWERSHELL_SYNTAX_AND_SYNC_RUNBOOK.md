# PowerShell Syntax and Synchronization Runbook

Validate all release scripts:

```powershell
.\scripts\release\Test-NrhisPowerShellSyntax.ps1 `
  -Paths @("scripts/release")
```

Synchronize `develop` without pruning:

```powershell
.\scripts\release\Update-NrhisDevelop.ps1 -Branch "develop"
```

Do not use automatic pruning during active build application or release
completion in the OneDrive-hosted repository.
