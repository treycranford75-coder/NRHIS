[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$base = $env:LOCALAPPDATA
if (-not $base) {
    $base = Join-Path $HOME "AppData\Local"
}

$root = Join-Path $base "NRHIS\handoff"
New-Item -ItemType Directory -Path $root -Force | Out-Null
return $root
