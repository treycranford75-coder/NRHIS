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
    -BuildNumber '093' `
    -RepositoryRoot $repo `
    -Tag 'v0.1.1-build093' `
    -ReleaseTitle 'NRHIS Sprint 2 Build093 - Installer Archive Lifecycle Guard' `
    -NotesFile 'C:\GitHub\NRHIS\docs\releases\BUILD093_RELEASE_NOTES.md'

if ($LASTEXITCODE -ne 0) {
    throw "Build093 canonical completion failed with exit code $LASTEXITCODE."
}
