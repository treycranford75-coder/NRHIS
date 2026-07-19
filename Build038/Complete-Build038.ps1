[CmdletBinding()]
param([string]$RepositoryRoot = (Get-Location).Path)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$repo = (Resolve-Path $RepositoryRoot).Path
Set-Location $repo
$script = Join-Path $repo "scripts\release\Invoke-NrhisOneStepLifecycle.ps1"
if (-not (Test-Path $script)) { throw "Build038 lifecycle helper is missing from the repository." }
& $script `
    -BuildNumber "038" `
    -Repository "treycranford75-coder/NRHIS" `
    -Branch "feature/sprint2-build038" `
    -CommitMessage "Build038: authenticate private-repository release verification" `
    -PullRequestTitle "Build038: authenticate private-repository release verification" `
    -PullRequestBodyFile (Join-Path $repo "docs\releases\BUILD038_PR.md") `
    -Tag "v0.1.1-rc38+build038" `
    -ReleaseTitle "NRHIS Sprint 2 Build038 - Authenticated Release Verification RC38" `
    -ReleaseNotesFile (Join-Path $repo "docs\releases\BUILD038_RELEASE_NOTES.md") `
    -PayloadRoot (Join-Path $PSScriptRoot "payload") `
    -EvidenceRoot (Join-Path $HOME "NRHIS-Release-Evidence")
