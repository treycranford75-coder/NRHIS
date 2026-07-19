# Bootstrap Order and Branch Safety Runbook

Start Build032 with:

```powershell
.\scripts\release\Start-NrhisBuild.ps1 -BuildNumber "032"
```

The build now installs the required bootstrap helpers before branch setup and
creates `feature/sprint2-build032` before any commit can occur.

Confirm the branch at any time:

```powershell
git branch --show-current
```

Expected:

```text
feature/sprint2-build032
```
