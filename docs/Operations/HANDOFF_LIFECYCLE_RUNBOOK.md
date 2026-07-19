# Handoff Lifecycle Runbook

Copy a Build028 PR description:

```powershell
.\scripts\release\Copy-NrhisHandoffSection.ps1 `
  -BuildNumber "028" `
  -Section PullRequestBody
```

Copy Build028 release notes:

```powershell
.\scripts\release\Copy-NrhisHandoffSection.ps1 `
  -BuildNumber "028" `
  -Section ReleaseNotes
```

Handoff files are stored outside the repository under:

```text
%LOCALAPPDATA%\NRHIS\handoff
```
