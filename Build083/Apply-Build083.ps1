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
    'src/nrhis_harvest/texaset_reservoir_evaporation.py',
    'config/nrhis/texaset_reservoir_evaporation.json',
    'scripts/Build-NrhisTexasETReservoirEvaporation.py',
    'tests/test_texaset_reservoir_evaporation_build083.py',
    'docs/Operations/BUILD083_TEXASET_RESERVOIR_EVAPORATION.md',
    'docs/releases/BUILD083.md',
    'docs/releases/BUILD083_PR.md',
    'docs/releases/BUILD083_RELEASE_NOTES.md'
)
foreach ($file in $files) { Copy-PayloadFile $file }

Set-Location $repo
python -m pytest tests/test_texaset_reservoir_evaporation_build083.py -q
if ($LASTEXITCODE -ne 0) { throw 'Build083 deterministic tests failed.' }

$branch = 'feature/sprint2-build083'
$existing = @(& git branch --list $branch) -join "`n"
if ([string]::IsNullOrWhiteSpace($existing)) {
    git switch -c $branch
} else {
    git switch $branch
}
git add -A
git commit -m 'Build083: integrate TexasET reservoir evaporation estimates'
if ($LASTEXITCODE -ne 0) { throw 'Build083 commit failed.' }
git push -u origin $branch
if ($LASTEXITCODE -ne 0) { throw 'Build083 push failed.' }
Write-Host 'Build083 applied and pushed.' -ForegroundColor Green
