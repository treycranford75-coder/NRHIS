[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Tag,

    [Parameter(Mandatory = $true)]
    [string]$ExpectedTitle,

    [Parameter(Mandatory = $true)]
    [string]$ExpectedNotesFile,

    [int]$TimeoutMinutes = 15,

    [int]$PollSeconds = 15
)

$ErrorActionPreference = "Stop"

$deadline = [DateTimeOffset]::UtcNow.AddMinutes($TimeoutMinutes)

while ([DateTimeOffset]::UtcNow -lt $deadline) {
    try {
        & .\scripts\release\Test-NrhisPublishedRelease.ps1 `
            -Tag $Tag `
            -ExpectedTitle $ExpectedTitle `
            -ExpectedNotesFile $ExpectedNotesFile

        exit 0
    }
    catch {
        Write-Host "Release not verified yet: $($_.Exception.Message)" -ForegroundColor Yellow
        Start-Sleep -Seconds $PollSeconds
    }
}

throw "Timed out waiting for published release $Tag after $TimeoutMinutes minute(s)."
