# Published Release Verification Runbook

Verify Build030 after publication:

```powershell
.\scripts\release\Test-NrhisPublishedRelease.ps1 `
  -Tag "v0.1.1-rc30+build030" `
  -ExpectedTitle "NRHIS Sprint 2 Build030 - Published Release Verification RC30" `
  -ExpectedNotesFile ".\docs\Release\Sprint2_Build030_Release_Notes.md"
```

Wait for the release to appear and verify it automatically:

```powershell
.\scripts\release\Wait-NrhisPublishedRelease.ps1 `
  -Tag "v0.1.1-rc30+build030" `
  -ExpectedTitle "NRHIS Sprint 2 Build030 - Published Release Verification RC30" `
  -ExpectedNotesFile ".\docs\Release\Sprint2_Build030_Release_Notes.md" `
  -TimeoutMinutes 15
```
