# Operator Handoff Runbook

After a build is applied, open:

```text
handoff/Build###_Operator_Handoff.md
```

Copy a specific value to the clipboard with:

```powershell
.\scriptselease\Copy-NrhisHandoffSection.ps1 `
  -BuildNumber "027" `
  -Section PullRequestBody
```

Supported sections:

- `PullRequestTitle`
- `PullRequestBody`
- `ReleaseTitle`
- `ReleaseNotes`
