[CmdletBinding()]
param([string]$RepositoryRoot = (Get-Location).Path)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path $RepositoryRoot).Path
Set-Location $repo
& (Join-Path $repo 'scripts/release/Complete-NrhisBuild.ps1') -BuildNumber '076' -RepositoryRoot $repo
