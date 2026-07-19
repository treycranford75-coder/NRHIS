[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$remoteUrl = (git remote get-url origin).Trim()
if (-not $remoteUrl) {
    throw "Unable to read the origin remote URL."
}

$patterns = @(
    "^git@github\.com:(?<slug>[^/]+/[^/]+?)(?:\.git)?$",
    "^ssh://git@github\.com/(?<slug>[^/]+/[^/]+?)(?:\.git)?$",
    "^https://github\.com/(?<slug>[^/]+/[^/]+?)(?:\.git)?/?$"
)

foreach ($pattern in $patterns) {
    if ($remoteUrl -match $pattern) {
        return $Matches["slug"]
    }
}

throw "Unsupported GitHub origin remote: $remoteUrl"
