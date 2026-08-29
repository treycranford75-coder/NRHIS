[CmdletBinding()]
param(
    [Parameter(Mandatory)][ValidatePattern('^\d{3}$')][string]$BuildNumber,
    [string]$RepositoryRoot = (Get-Location).Path,
    [Parameter(Mandatory)][string]$Tag,
    [Parameter(Mandatory)][string]$ReleaseTitle,
    [Parameter(Mandatory)][string]$NotesFile
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
$buildDirectory = Join-Path $repo "Build$BuildNumber"
New-Item -ItemType Directory -Path $buildDirectory -Force | Out-Null
$wrapperPath = Join-Path $buildDirectory "Complete-Build$BuildNumber.ps1"

function ConvertTo-SingleQuotedLiteral {
    param([Parameter(Mandatory)][string]$Value)
    return "'" + $Value.Replace("'", "''") + "'"
}

$tagLiteral = ConvertTo-SingleQuotedLiteral -Value $Tag
$titleLiteral = ConvertTo-SingleQuotedLiteral -Value $ReleaseTitle
$notesLiteral = ConvertTo-SingleQuotedLiteral -Value $NotesFile

$content = @"
[CmdletBinding()]
param(
    [string]`$RepositoryRoot = (Get-Location).Path
)

`$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

`$repo = (Resolve-Path `$RepositoryRoot).Path
`$completionHelper = Join-Path `$repo 'scripts/release/Complete-NrhisBuild.ps1'
if (-not (Test-Path `$completionHelper -PathType Leaf)) {
    throw "Canonical completion helper not found: `$completionHelper"
}

& powershell.exe -NoProfile -ExecutionPolicy Bypass -File `$completionHelper ``
    -BuildNumber '$BuildNumber' ``
    -RepositoryRoot `$repo ``
    -Tag $tagLiteral ``
    -ReleaseTitle $titleLiteral ``
    -NotesFile $notesLiteral

if (`$LASTEXITCODE -ne 0) {
    throw "Build$BuildNumber canonical completion failed with exit code `$LASTEXITCODE."
}
"@

[System.IO.File]::WriteAllText(
    $wrapperPath,
    $content.TrimStart() + "`n",
    [System.Text.UTF8Encoding]::new($false)
)

$tokens = $null
$errors = $null
[void][System.Management.Automation.Language.Parser]::ParseFile(
    $wrapperPath,
    [ref]$tokens,
    [ref]$errors
)
if ($errors.Count -gt 0) {
    $messages = @($errors | ForEach-Object { $_.Message }) -join '; '
    throw "Generated completion wrapper is invalid: $messages"
}

$rendered = Get-Content $wrapperPath -Raw
if ($rendered -notmatch '\[CmdletBinding\(\)\]\s*param\(') {
    throw 'Generated completion wrapper is missing the CmdletBinding/param contract.'
}
if ($rendered -notmatch '\[string\]\$RepositoryRoot') {
    throw 'Generated completion wrapper does not accept -RepositoryRoot.'
}
if ($rendered -notmatch 'Complete-NrhisBuild\.ps1') {
    throw 'Generated completion wrapper does not delegate to Complete-NrhisBuild.ps1.'
}

Write-Host "Completion wrapper ready: $wrapperPath" -ForegroundColor Green
