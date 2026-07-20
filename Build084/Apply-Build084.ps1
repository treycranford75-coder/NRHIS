[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RepositoryRoot
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repo = (Resolve-Path $RepositoryRoot).Path
$payload = Join-Path $PSScriptRoot 'payload'

function Copy-PayloadFile {
    param([Parameter(Mandatory)][string]$RelativePath)
    $source = Join-Path $payload $RelativePath
    $destination = Join-Path $repo $RelativePath
    if (-not (Test-Path $source -PathType Leaf)) { throw "Payload file missing: $source" }
    New-Item -ItemType Directory -Path (Split-Path $destination -Parent) -Force | Out-Null
    if (([System.IO.Path]::GetFullPath($source)).Equals([System.IO.Path]::GetFullPath($destination), [System.StringComparison]::OrdinalIgnoreCase)) { return }
    Copy-Item $source $destination -Force
}

$files = @(
    'src/nrhis_harvest/reservoir_evaporation_rollup.py',
    'config/nrhis/reservoir_evaporation_rollup.json',
    'scripts/Build-NrhisReservoirEvaporationRollup.py',
    'tests/test_reservoir_evaporation_rollup_build084.py',
    'docs/Operations/BUILD084_RESERVOIR_EVAPORATION_ROLLUPS.md',
    'docs/releases/BUILD084.md',
    'docs/releases/BUILD084_PR.md',
    'docs/releases/BUILD084_RELEASE_NOTES.md'
)
foreach ($file in $files) { Copy-PayloadFile $file }

Set-Location $repo
python -m pytest tests/test_reservoir_evaporation_rollup_build084.py -q
if ($LASTEXITCODE -ne 0) { throw 'Build084 deterministic tests failed.' }

$branch = 'feature/sprint2-build084'
$existing = @(& git branch --list $branch) -join "`n"
if ([string]::IsNullOrWhiteSpace($existing)) { git switch -c $branch } else { git switch $branch }
git add -A
git commit -m 'Build084: add reservoir evaporation rollups to daily operations'
if ($LASTEXITCODE -ne 0) { throw 'Build084 commit failed.' }
git push -u origin $branch
if ($LASTEXITCODE -ne 0) { throw 'Build084 push failed.' }
Write-Host 'Build084 applied and pushed.' -ForegroundColor Green
