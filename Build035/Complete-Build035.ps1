[CmdletBinding()]
param(
    [string]$ExpectedTag = "v0.1.1-rc35+build035",
    [string]$EvidenceRoot = (Join-Path $HOME "NRHIS-Release-Evidence")
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$repo = (Get-Location).Path
if (-not (Test-Path (Join-Path $repo ".git"))) { throw "Run from the NRHIS repository root." }
if ((git branch --show-current).Trim() -ne "develop") { throw "Switch to develop after the Build035 PR is merged." }

git fetch origin --no-prune
git pull --ff-only --no-prune origin develop
$expectedCommit = (git rev-parse HEAD).Trim()

$handoffRoot = Join-Path $EvidenceRoot "Build035"
New-Item -ItemType Directory -Path $handoffRoot -Force | Out-Null
$handoff = [ordered]@{
    build = "035"
    tag = $ExpectedTag
    expected_merged_commit = $expectedCommit
    release_title = "NRHIS Sprint 2 Build035 - Release Verification Closure RC35"
    prerelease = $true
    latest = $false
    generated_utc = [DateTime]::UtcNow.ToString("o")
    verification_command = ".\scripts\release\Close-NrhisReleaseVerification.ps1 -BuildNumber '035' -Tag '$ExpectedTag' -ExpectedCommit '$expectedCommit' -EvidenceJson '<PUBLIC-RELEASE-VERIFICATION-JSON>'"
}
$handoffPath = Join-Path $handoffRoot "publication-handoff.json"
$handoff | ConvertTo-Json -Depth 6 | Set-Content $handoffPath -Encoding utf8
Set-Clipboard -Value $handoff.verification_command -ErrorAction SilentlyContinue

Write-Host "Build035 publication handoff prepared." -ForegroundColor Cyan
Write-Host "Publish as a pre-release and do not mark it latest."
Write-Host "Expected merged commit: $expectedCommit"
Write-Host "Handoff: $handoffPath"
Write-Host "After public verification JSON exists, run the copied closure command."
Write-Host "Build035 is not complete until completion-receipt.json exists." -ForegroundColor Yellow
