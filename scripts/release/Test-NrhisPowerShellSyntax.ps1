[CmdletBinding()]
param(
    [string[]]$Paths = @("scripts/release")
)

$ErrorActionPreference = "Stop"

$files = foreach ($path in $Paths) {
    if (-not (Test-Path $path)) {
        throw "PowerShell syntax path not found: $path"
    }

    Get-ChildItem $path -Recurse -File -Filter "*.ps1"
}

$failures = [System.Collections.Generic.List[object]]::new()

foreach ($file in $files) {
    $tokens = $null
    $errors = $null

    [System.Management.Automation.Language.Parser]::ParseFile(
        $file.FullName,
        [ref]$tokens,
        [ref]$errors
    ) | Out-Null

    foreach ($error in $errors) {
        $failures.Add([pscustomobject]@{
            file = $file.FullName
            message = $error.Message
            line = $error.Extent.StartLineNumber
            column = $error.Extent.StartColumnNumber
        })
    }
}

if ($failures.Count -gt 0) {
    $failures | Format-Table -AutoSize
    throw "PowerShell syntax validation failed for $($failures.Count) error(s)."
}

Write-Host ""
Write-Host "PowerShell syntax validation passed for $($files.Count) script(s)." -ForegroundColor Green
