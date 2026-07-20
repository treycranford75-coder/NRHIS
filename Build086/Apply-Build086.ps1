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
    'scripts/release/Finish-NrhisBuildLifecycle.ps1',
    'tests/test_release_ci_registration_build086.py',
    'docs/Operations/BUILD086_CI_REGISTRATION_RETRY.md',
    'docs/releases/BUILD086.md',
    'docs/releases/BUILD086_PR.md',
    'docs/releases/BUILD086_RELEASE_NOTES.md'
)
foreach ($file in $files) { Copy-PayloadFile $file }

Set-Location $repo
python -m pytest tests/test_release_ci_registration_build086.py -q
if ($LASTEXITCODE -ne 0) { throw 'Build086 deterministic tests failed.' }

$tokens = $null
$errors = $null
[void][System.Management.Automation.Language.Parser]::ParseFile(
    (Resolve-Path 'scripts/release/Finish-NrhisBuildLifecycle.ps1'),
    [ref]$tokens,
    [ref]$errors
)
if ($errors.Count -gt 0) {
    $errors | ForEach-Object { Write-Error $_.Message }
    throw 'Build086 PowerShell syntax validation failed.'
}

$branch = 'feature/sprint2-build086'
$existing = @(& git branch --list $branch) -join "`n"
if ([string]::IsNullOrWhiteSpace($existing)) { git switch -c $branch } else { git switch $branch }
git add -A
git commit -m 'Build086: retry pending CI registration before failure'
if ($LASTEXITCODE -ne 0) { throw 'Build086 commit failed.' }
git push -u origin $branch
if ($LASTEXITCODE -ne 0) { throw 'Build086 push failed.' }
Write-Host 'Build086 applied and pushed.' -ForegroundColor Green
