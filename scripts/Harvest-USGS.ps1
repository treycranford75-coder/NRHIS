[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)]
    [string]$Registry = "config/stations/lower_nueces.yml",

    [Parameter(Mandatory = $false)]
    [string]$StartDate,

    [Parameter(Mandatory = $false)]
    [string]$EndDate,

    [Parameter(Mandatory = $false)]
    [ValidateRange(1, 3660)]
    [int]$Days = 2,

    [Parameter(Mandatory = $false)]
    [string]$OutputRoot = "data",

    [Parameter(Mandatory = $false)]
    [ValidateRange(1, 600)]
    [int]$TimeoutSeconds = 60
)

$ErrorActionPreference = "Stop"
$RepoRoot = Split-Path -Parent $PSScriptRoot
$LogDirectory = Join-Path $RepoRoot "reports/logs"
$LogFile = Join-Path $LogDirectory ("harvest-usgs-{0}.log" -f (Get-Date -Format "yyyyMMddTHHmmss"))
New-Item -ItemType Directory -Force -Path $LogDirectory | Out-Null

$Python = if (Get-Command python -ErrorAction SilentlyContinue) {
    "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    "py"
} else {
    throw "Python 3.11 or newer was not found on PATH."
}

$Arguments = @(
    "-m", "nrhis_harvest.cli",
    "--registry", (Join-Path $RepoRoot $Registry),
    "--output-root", (Join-Path $RepoRoot $OutputRoot),
    "--days", $Days,
    "--timeout", $TimeoutSeconds,
    "--log-file", $LogFile
)
if ($StartDate) { $Arguments += @("--start", $StartDate) }
if ($EndDate) { $Arguments += @("--end", $EndDate) }

$PreviousPythonPath = $env:PYTHONPATH
$SourcePath = Join-Path $RepoRoot "src"
$env:PYTHONPATH = if ($PreviousPythonPath) { "$SourcePath;$PreviousPythonPath" } else { $SourcePath }
try {
    & $Python @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "USGS harvest failed with exit code $LASTEXITCODE. See $LogFile"
    }
}
finally {
    $env:PYTHONPATH = $PreviousPythonPath
}
