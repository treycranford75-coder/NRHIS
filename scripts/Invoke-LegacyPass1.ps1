[CmdletBinding()]
param(
    [string]$OutputRoot = "reports/legacy-pass1",
    [string[]]$ExtraArgs = @(),
    [double]$TimeoutSeconds,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$repositoryRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
Push-Location $repositoryRoot

try {
    $arguments = @(
        "-m",
        "nrhis_calibration.legacy_cli",
        "--output-root",
        $OutputRoot
    )

    if ($DryRun) {
        $arguments += "--dry-run"
    }

    if ($PSBoundParameters.ContainsKey("TimeoutSeconds")) {
        $arguments += "--timeout-seconds"
        $arguments += [string]$TimeoutSeconds
    }

    foreach ($argument in $ExtraArgs) {
        $arguments += "--extra-arg"
        $arguments += $argument
    }

    python @arguments

    if ($LASTEXITCODE -ne 0) {
        throw "Legacy Pass1 wrapper failed with exit code $LASTEXITCODE."
    }
}
finally {
    Pop-Location
}
