[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$Tag,

    [Parameter(Mandatory = $true)]
    [string]$ReleaseTitle,

    [Parameter(Mandatory = $true)]
    [string]$ReleaseNotesFile,

    [int]$TimeoutMinutes = 15
)

$escapedTag = $Tag.Replace('"', '\"')
$escapedTitle = $ReleaseTitle.Replace('"', '\"')
$escapedNotes = $ReleaseNotesFile.Replace('"', '\"')

@"
.\scripts\release\Wait-NrhisPublishedRelease.ps1 `
  -Tag "$escapedTag" `
  -ExpectedTitle "$escapedTitle" `
  -ExpectedNotesFile "$escapedNotes" `
  -TimeoutMinutes $TimeoutMinutes
"@.Trim()
