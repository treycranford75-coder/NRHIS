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
    -BuildNumber '096' `
    -RepositoryRoot $repo `
    -Tag 'v0.1.1-build096' `
    -ReleaseTitle 'NRHIS Sprint 2 Build096 - Historical Query CLI Hardening' `
    -NotesFile 'C:\GitHub\NRHIS\docs\releases\BUILD096_RELEASE_NOTES.md'

if ($LASTEXITCODE -ne 0) {
    throw "Build096 canonical completion failed with exit code $LASTEXITCODE."
}
