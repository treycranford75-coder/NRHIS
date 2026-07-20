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
    'src/nrhis_harvest/texaset_et_harvest.py',
    'config/nrhis/texaset_regions.json',
    'scripts/Build-NrhisTexasETRegionalSummary.py',
    'tests/test_texaset_et_regions_build082.py',
    'docs/Operations/BUILD082_TEXASET_REGIONAL_ET.md',
    'docs/releases/BUILD082.md',
    'docs/releases/BUILD082_PR.md',
    'docs/releases/BUILD082_RELEASE_NOTES.md'
)
foreach ($file in $files) { Copy-PayloadFile $file }

python -m pytest tests/test_texaset_et_regions_build082.py -q
if ($LASTEXITCODE -ne 0) { throw 'Build082 deterministic tests failed.' }

Set-Location $repo
git switch -c feature/sprint2-build082
git add -A
git commit -m 'Build082: add TexasET Coastal Bend and Winter Garden ET'
git push -u origin feature/sprint2-build082
Write-Host 'Build082 applied and pushed.' -ForegroundColor Green
