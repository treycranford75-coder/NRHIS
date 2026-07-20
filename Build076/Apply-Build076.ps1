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
python -m pytest tests/test_release_lifecycle_state_build076.py -q
if ($LASTEXITCODE -ne 0) { throw 'Build076 tests failed.' }
$branch = 'feature/sprint2-build076'
git switch -C $branch
git add -A
git commit -m 'Build076: add lifecycle state receipts'
git push --force-with-lease origin $branch
Write-Host 'Build076 applied and pushed.' -ForegroundColor Green
