[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$RepositoryRoot
)

$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$repo = (Resolve-Path $RepositoryRoot).Path
$payload = Join-Path $PSScriptRoot 'payload'

function Copy-PayloadFile {
    param([Parameter(Mandatory)][string]$RelativePath)
    $source = Join-Path $payload $RelativePath
    $destination = Join-Path $repo $RelativePath
    if (-not (Test-Path $source -PathType Leaf)) { throw "Payload file missing: $source" }
    $parent = Split-Path $destination -Parent
    New-Item -ItemType Directory -Path $parent -Force | Out-Null
    if (([System.IO.Path]::GetFullPath($source)).Equals([System.IO.Path]::GetFullPath($destination), [System.StringComparison]::OrdinalIgnoreCase)) {
        Write-Host "Already in place: $RelativePath" -ForegroundColor DarkGray
        return
    }
    Copy-Item $source $destination -Force
}

Copy-PayloadFile 'scripts/release/Resolve-NrhisPullRequest.ps1'
Copy-PayloadFile 'tests/test_release_pr_resolution_build081.py'
Copy-PayloadFile 'docs/Operations/BUILD081_AUTOMATIC_PR_RESOLUTION.md'
Copy-PayloadFile 'docs/releases/BUILD081.md'
Copy-PayloadFile 'docs/releases/BUILD081_PR.md'
Copy-PayloadFile 'docs/releases/BUILD081_RELEASE_NOTES.md'

$finishPath = Join-Path $repo 'scripts/release/Finish-NrhisBuildLifecycle.ps1'
if (-not (Test-Path $finishPath -PathType Leaf)) { throw "Required lifecycle helper not found: $finishPath" }
$finish = Get-Content $finishPath -Raw

$marker = '# Build081 automatic pull-request resolution'
if (-not $finish.Contains($marker)) {
    $paramEnd = $finish.IndexOf("`n)")
    if ($paramEnd -lt 0) { throw 'Unable to locate Finish-NrhisBuildLifecycle parameter block.' }

    $anchor = '$ErrorActionPreference = ''Stop'''
    if (-not $finish.Contains($anchor)) { throw 'Unable to locate lifecycle initialization anchor.' }

    $insertion = @'
# Build081 automatic pull-request resolution
$placeholderValues = @(
    'PASTE_ACTUAL_PR_URL_HERE',
    'PASTE_THE_PR_URL_RETURNED_ABOVE',
    'PASTE_PR_URL_HERE'
)

$needsResolution = [string]::IsNullOrWhiteSpace($PullRequestUrl) -or ($placeholderValues -contains $PullRequestUrl.Trim())
if ($needsResolution) {
    $resolver = Join-Path $RepositoryRoot 'scripts/release/Resolve-NrhisPullRequest.ps1'
    if (-not (Test-Path $resolver -PathType Leaf)) {
        throw "Pull-request resolver not found: $resolver"
    }

    $PullRequestUrl = & $resolver -BuildNumber $BuildNumber -RepositoryRoot $RepositoryRoot
}

if ($PullRequestUrl -notmatch '^https://github\.com/[^/]+/[^/]+/pull/\d+$') {
    throw "Invalid pull-request URL: $PullRequestUrl"
}
'@
    $finish = $finish.Replace($anchor, "$anchor`r`n`r`n$insertion")
    [System.IO.File]::WriteAllText($finishPath, $finish, [System.Text.UTF8Encoding]::new($false))
}

python -m pytest tests/test_release_pr_resolution_build081.py -q
if ($LASTEXITCODE -ne 0) { throw 'Build081 deterministic tests failed.' }

Set-Location $repo
git switch -c feature/sprint2-build081

git add -A
git commit -m 'Build081: automate pull-request URL resolution'
git push -u origin feature/sprint2-build081

Write-Host 'Build081 applied and pushed.' -ForegroundColor Green
Write-Host 'Start-NrhisBuild can now resolve the PR URL automatically.' -ForegroundColor Green
