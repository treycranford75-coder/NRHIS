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
    'scripts/release/release-lifecycle-contract.json',
    'scripts/release/validate_release_lifecycle_contract.py',
    'tests/test_release_lifecycle_contract_build087.py',
    'docs/Operations/BUILD087_STRUCTURED_LIFECYCLE_CONTRACT.md',
    'docs/releases/BUILD087.md',
    'docs/releases/BUILD087_PR.md',
    'docs/releases/BUILD087_RELEASE_NOTES.md'
)
foreach ($file in $files) { Copy-PayloadFile $file }

Set-Location $repo
python -m ruff check scripts/release/validate_release_lifecycle_contract.py tests/test_release_lifecycle_contract_build087.py
if ($LASTEXITCODE -ne 0) { throw 'Build087 Ruff validation failed.' }

python -m pytest tests/test_release_lifecycle_contract_build087.py -q
if ($LASTEXITCODE -ne 0) { throw 'Build087 deterministic tests failed.' }

python scripts/release/validate_release_lifecycle_contract.py
if ($LASTEXITCODE -ne 0) { throw 'Build087 lifecycle contract validation failed.' }

$branch = 'feature/sprint2-build087'
$existing = @(& git branch --list $branch) -join "`n"
if ([string]::IsNullOrWhiteSpace($existing)) { git switch -c $branch } else { git switch $branch }
git add -A
git commit -m 'Build087: add structured release lifecycle contract'
if ($LASTEXITCODE -ne 0) { throw 'Build087 commit failed.' }
git push -u origin $branch
if ($LASTEXITCODE -ne 0) { throw 'Build087 push failed.' }
Write-Host 'Build087 applied and pushed.' -ForegroundColor Green
