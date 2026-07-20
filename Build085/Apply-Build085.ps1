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
    'src/nrhis_harvest/reservoir_water_budget.py',
    'config/nrhis/reservoir_water_budget.json',
    'scripts/Build-NrhisReservoirWaterBudget.py',
    'tests/test_reservoir_water_budget_build085.py',
    'docs/Operations/BUILD085_RESERVOIR_WATER_BUDGETS.md',
    'docs/releases/BUILD085.md',
    'docs/releases/BUILD085_PR.md',
    'docs/releases/BUILD085_RELEASE_NOTES.md'
)
foreach ($file in $files) { Copy-PayloadFile $file }

Set-Location $repo
python -m pytest tests/test_reservoir_water_budget_build085.py -q
if ($LASTEXITCODE -ne 0) { throw 'Build085 deterministic tests failed.' }
python -m ruff check src/nrhis_harvest/reservoir_water_budget.py scripts/Build-NrhisReservoirWaterBudget.py tests/test_reservoir_water_budget_build085.py
if ($LASTEXITCODE -ne 0) { throw 'Build085 Ruff validation failed.' }

$branch = 'feature/sprint2-build085'
$existing = @(& git branch --list $branch) -join "`n"
if ([string]::IsNullOrWhiteSpace($existing)) { git switch -c $branch } else { git switch $branch }
git add -A
git commit -m 'Build085: integrate reservoir evaporation into daily water budgets'
if ($LASTEXITCODE -ne 0) { throw 'Build085 commit failed.' }
git push -u origin $branch
if ($LASTEXITCODE -ne 0) { throw 'Build085 push failed.' }
Write-Host 'Build085 applied and pushed.' -ForegroundColor Green
