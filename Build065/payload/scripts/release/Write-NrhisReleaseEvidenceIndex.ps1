[CmdletBinding()]
param([string]$EvidenceRoot = (Join-Path $HOME "NRHIS-Release-Evidence"))

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
New-Item -ItemType Directory -Path $EvidenceRoot -Force | Out-Null

$items = @()
Get-ChildItem $EvidenceRoot -Directory -Filter "Build*" | Sort-Object Name | ForEach-Object {
    $receiptPath = Join-Path $_.FullName "completion-receipt.json"
    if (Test-Path $receiptPath) {
        $receipt = Get-Content $receiptPath -Raw | ConvertFrom-Json
        $items += [ordered]@{
            build = [string]$receipt.build
            tag = [string]$receipt.tag
            expected_commit = [string]$receipt.expected_commit
            verified_commit = [string]$receipt.verified_commit
            verified_utc = [string]$receipt.verified_utc
            status = [string]$receipt.status
            receipt = $receiptPath
            evidence = [string]$receipt.evidence_file
        }
    }
}

$index = [ordered]@{
    schema_version = 1
    generated_utc = [DateTime]::UtcNow.ToString("o")
    evidence_root = $EvidenceRoot
    completed_builds = $items
}
$indexPath = Join-Path $EvidenceRoot "release-evidence-index.json"
$index | ConvertTo-Json -Depth 8 | Set-Content $indexPath -Encoding utf8

$lines = @("# NRHIS Release Verification Index", "", "Generated: $($index.generated_utc)", "")
foreach ($item in $items) {
    $lines += "- Build$($item.build) | $($item.tag) | $($item.status) | $($item.verified_commit)"
}
$lines | Set-Content (Join-Path $EvidenceRoot "release-evidence-index.md") -Encoding utf8
Write-Host "Evidence index updated: $indexPath"
