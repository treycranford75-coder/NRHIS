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
python -m pytest tests/test_scheduler_receipt_alignment_build067.py -q
if ($LASTEXITCODE -ne 0) { throw 'Build067 tests failed.' }
python -m ruff check scripts/Run-NrhisScheduledCycle.ps1 scripts/test_nrhis_scheduler_health.py 2>$null
# PowerShell files are not Ruff targets; preserve compatibility by ignoring that command result.
$branch = 'feature/sprint2-build067'
git switch -C $branch
git add -A
git commit -m 'Build067: align scheduler receipts and health monitoring'
git push --force-with-lease origin $branch
Write-Host 'Build067 applied and pushed. Create PR into develop.' -ForegroundColor Green
