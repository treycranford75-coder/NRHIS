[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path,
    [switch]$NoChain,
    [switch]$NoArchive
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repo = (Resolve-Path $RepositoryRoot).Path
if (-not (Test-Path (Join-Path $repo '.git'))) { throw 'Run from the NRHIS repository root.' }
Set-Location $repo
$payload = Join-Path $PSScriptRoot 'payload'
Get-ChildItem $payload -Recurse -File | ForEach-Object {
    $relative = $_.FullName.Substring($payload.Length).TrimStart([char[]]@('\','/'))
    $dest = Join-Path $repo $relative
    New-Item -ItemType Directory -Path (Split-Path $dest -Parent) -Force | Out-Null
    Copy-Item $_.FullName $dest -Force
}
python -m ruff check tests/test_release_pr_automation_build071.py
if ($LASTEXITCODE -ne 0) { throw 'Build071 Ruff gate failed.' }
python -m pytest tests/test_release_pr_automation_build071.py -q
if ($LASTEXITCODE -ne 0) { throw 'Build071 tests failed.' }
$tokens = $null
$errors = $null
[void][System.Management.Automation.Language.Parser]::ParseFile((Join-Path $repo 'scripts/release/New-NrhisPullRequest.ps1'), [ref]$tokens, [ref]$errors)
if ($errors.Count -gt 0) { throw 'Build071 PR helper PowerShell syntax gate failed.' }
$tokens = $null
$errors = $null
[void][System.Management.Automation.Language.Parser]::ParseFile((Join-Path $repo 'scripts/release/Start-NrhisBuild.ps1'), [ref]$tokens, [ref]$errors)
if ($errors.Count -gt 0) { throw 'Build071 start-build PowerShell syntax gate failed.' }
$branch = 'feature/sprint2-build071'
git switch -C $branch
git add -A
git commit -m 'Build071: automate pull-request creation in one-step lifecycle'
git push --force-with-lease origin $branch
$helper = Join-Path $repo 'scripts/release/New-NrhisPullRequest.ps1'
$body = Join-Path $repo 'docs/releases/BUILD071_PR.md'
$prUrl = & $helper -Branch $branch -Base 'develop' -Title 'Build071: automate pull-request creation in the one-step lifecycle' -BodyFile $body -RepositoryRoot $repo
Write-Host 'Build071 applied and pushed.' -ForegroundColor Green
Write-Host "Pull request ready: $prUrl" -ForegroundColor Green
Write-Host 'Waiting for CI and merge into develop.' -ForegroundColor Yellow
