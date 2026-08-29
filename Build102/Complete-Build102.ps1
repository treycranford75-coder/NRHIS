[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
$completionHelper = Join-Path $repo 'scripts/release/Complete-NrhisBuild.ps1'
if (-not (Test-Path $completionHelper -PathType Leaf)) {
    throw "Canonical completion helper not found: $completionHelper"
}

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File $completionHelper `
    -BuildNumber '102' `
    -RepositoryRoot $repo `
    -Tag 'v0.1.1-build102' `
    -ReleaseTitle 'NRHIS Sprint 2 Build102 - Lower Nueces Lag Stability and Reach Residuals' `
    -NotesFile 'C:\GitHub\NRHIS\docs\releases\BUILD102_RELEASE_NOTES.md'

if ($LASTEXITCODE -ne 0) {
    throw "Build102 canonical completion failed with exit code $LASTEXITCODE."
}
