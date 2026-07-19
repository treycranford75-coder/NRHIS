[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$PayloadRoot,

    [string[]]$AdditionalFiles = @()
)

$ErrorActionPreference = "Stop"

$resolvedPayloadRoot = (Resolve-Path $PayloadRoot).Path
$repoRoot = (Get-Location).Path
$files = [System.Collections.Generic.List[string]]::new()

Get-ChildItem $resolvedPayloadRoot -Recurse -File | ForEach-Object {
    $relative = $_.FullName.Substring($resolvedPayloadRoot.Length).TrimStart([char[]]"\/")
    $files.Add($relative.Replace("\", "/"))
}

foreach ($additional in $AdditionalFiles) {
    if (-not (Test-Path $additional)) {
        throw "Additional build file not found: $additional"
    }

    $resolved = (Resolve-Path $additional).Path
    if (-not $resolved.StartsWith($repoRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Additional build file is outside the repository: $additional"
    }

    $relative = $resolved.Substring($repoRoot.Length).TrimStart([char[]]"\/")
    $files.Add($relative.Replace("\", "/"))
}

$files |
    Sort-Object -Unique |
    ForEach-Object { $_ }
