[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$PayloadRoot
)

$ErrorActionPreference = "Stop"

$resolvedPayloadRoot = (Resolve-Path $PayloadRoot).Path
$repoRoot = (Get-Location).Path
$mismatches = [System.Collections.Generic.List[string]]::new()

Get-ChildItem $resolvedPayloadRoot -Recurse -File | ForEach-Object {
    $relative = $_.FullName.Substring($resolvedPayloadRoot.Length).TrimStart([char[]]"\/")
    $destination = Join-Path $repoRoot $relative

    if (-not (Test-Path $destination)) {
        $mismatches.Add("Missing working-tree file: $relative")
        return
    }

    $payloadHash = (Get-FileHash $_.FullName -Algorithm SHA256).Hash
    $workingHash = (Get-FileHash $destination -Algorithm SHA256).Hash

    if ($payloadHash -ne $workingHash) {
        $mismatches.Add("Payload mismatch: $relative")
    }
}

if ($mismatches.Count -gt 0) {
    $mismatches | ForEach-Object { Write-Host $_ -ForegroundColor Red }
    throw "Payload consistency verification failed."
}

Write-Host ""
Write-Host "Payload consistency verification passed." -ForegroundColor Green
