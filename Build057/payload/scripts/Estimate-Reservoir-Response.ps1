[CmdletBinding()]
param(
    [string]$Config = "config/nrhis/reservoir_response.json",
    [string]$DataRoot = "data/nrhis"
)
$ErrorActionPreference = "Stop"
python .\scripts\estimate_reservoir_response.py --config $Config --data-root $DataRoot
if ($LASTEXITCODE -ne 0) { throw "Reservoir response estimation failed with exit code $LASTEXITCODE." }
