[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$PayloadRoot,

    [string[]]$BootstrapFiles = @()
)

$ErrorActionPreference = "Stop"

$resolvedPayloadRoot = (Resolve-Path $PayloadRoot).Path
$repoRoot = (Get-Location).Path

function Install-RelativeFile {
    param(
        [string]$RelativePath
    )

    $source = Join-Path $resolvedPayloadRoot $RelativePath
    if (-not (Test-Path $source)) {
        throw "Payload file not found: $RelativePath"
    }

    $destination = Join-Path $repoRoot $RelativePath
    New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
    Copy-Item $source $destination -Force
    Write-Host "Installed: $RelativePath"
}

foreach ($bootstrapFile in $BootstrapFiles) {
    Install-RelativeFile -RelativePath $bootstrapFile
}

Get-ChildItem $resolvedPayloadRoot -Recurse -File | ForEach-Object {
    $relative = $_.FullName.Substring($resolvedPayloadRoot.Length).TrimStart([char[]]"\/")
    $relative = $relative.Replace("\", "/")

    if ($relative -in $BootstrapFiles) {
        return
    }

    Install-RelativeFile -RelativePath $relative
}
