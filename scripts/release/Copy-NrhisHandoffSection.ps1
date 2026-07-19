[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$BuildNumber,

    [ValidateSet("PullRequestTitle", "PullRequestBody", "ReleaseTitle", "ReleaseNotes")]
    [string]$Section
)

$ErrorActionPreference = "Stop"

$handoffPath = ".\handoff\Build${BuildNumber}_Operator_Handoff.md"
if (-not (Test-Path $handoffPath)) {
    throw "Operator handoff not found: $handoffPath"
}

$content = Get-Content $handoffPath -Raw

switch ($Section) {
    "PullRequestTitle" {
        $value = [regex]::Match($content, '(?m)^- Title: (.+)$').Groups[1].Value
    }
    "PullRequestBody" {
        $value = [regex]::Match(
            $content,
            '(?s)### Pull-request description\r?\n\r?\n(.*?)\r?\n\r?\n## Release'
        ).Groups[1].Value
    }
    "ReleaseTitle" {
        $matches = [regex]::Matches($content, '(?m)^- Title: (.+)$')
        $value = $matches[$matches.Count - 1].Groups[1].Value
    }
    "ReleaseNotes" {
        $value = [regex]::Match(
            $content,
            '(?s)### Release notes\r?\n\r?\n(.*)$'
        ).Groups[1].Value.TrimEnd()
    }
}

if (-not $value) {
    throw "Unable to extract section $Section from $handoffPath."
}

Set-Clipboard -Value $value
Write-Host "$Section copied to clipboard." -ForegroundColor Green
