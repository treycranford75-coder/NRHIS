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
python -m ruff check scripts/build_scheduler_alert.py tests/test_scheduler_alert_build069.py
if ($LASTEXITCODE -ne 0) { throw 'Build069 Ruff gate failed.' }
python -m pytest tests/test_scheduler_alert_build069.py -q
if ($LASTEXITCODE -ne 0) { throw 'Build069 tests failed.' }
$branch = 'feature/sprint2-build069'
git switch -C $branch
git add -A
git commit -m 'Build069: add scheduler alert artifacts and history'
git push --force-with-lease origin $branch
Write-Host 'Build069 applied and pushed. Create PR into develop.' -ForegroundColor Green
