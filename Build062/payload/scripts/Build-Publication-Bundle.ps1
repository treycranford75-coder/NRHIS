[CmdletBinding()]
param(
    [string]$Config = "config/nrhis/publication_bundle.json",
    [string]$DataRoot = "data/nrhis",
    [ValidateRange(0, 2)][int]$QaPassesCompleted = 0
)
$ErrorActionPreference = "Stop"
python -m scripts.build_publication_bundle --config $Config --data-root $DataRoot --qa-passes-completed $QaPassesCompleted
if ($LASTEXITCODE -ne 0) { throw "Build061 publication bundle failed with exit code $LASTEXITCODE" }
