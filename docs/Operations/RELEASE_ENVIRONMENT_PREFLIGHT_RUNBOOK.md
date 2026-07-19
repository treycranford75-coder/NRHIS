# Release Environment Preflight Runbook

Run the standard preflight:

```powershell
.\scriptselease\Test-NrhisReleaseEnvironment.ps1
```

Require GitHub CLI and authentication:

```powershell
.\scriptselease\Test-NrhisReleaseEnvironment.ps1 -RequireGitHubCli
```

Install GitHub CLI through winget:

```powershell
.\scriptselease\Initialize-NrhisGitHubCli.ps1 -Install
```

Authenticate GitHub CLI:

```powershell
.\scriptselease\Initialize-NrhisGitHubCli.ps1 -Authenticate
```

Publish a release for an existing pushed tag:

```powershell
.\scriptselease\Publish-NrhisExistingRelease.ps1 `
  -Tag "v0.1.1-rc25+build025" `
  -ReleaseTitle "NRHIS Sprint 2 Build025 - Release Environment Preflight RC25" `
  -ReleaseNotesFile ".\docs\Release\Sprint2_Build025_Release_Notes.md"
```
