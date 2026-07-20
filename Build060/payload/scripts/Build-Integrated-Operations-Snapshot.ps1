[CmdletBinding()]
param(
    [string]$Config = "config/nrhis/integrated_operations_snapshot.json",
    [string]$DataRoot = "data/nrhis",
    [switch]$RefreshSources
)
$ErrorActionPreference = "Stop"
if ($RefreshSources) {
    & "$PSScriptRoot/Harvest-USGS-Production.ps1"
    & "$PSScriptRoot/Harvest-NWPS-Forecasts.ps1"
    & "$PSScriptRoot/Harvest-TWDB-Reservoirs.ps1"
    & "$PSScriptRoot/Harvest-SALT03-Coastal.ps1"
    & "$PSScriptRoot/Build-Reservoir-Operations-Summary.ps1"
}
python "$PSScriptRoot/build_integrated_operations_snapshot.py" --config $Config --data-root $DataRoot
if ($LASTEXITCODE -ne 0) { throw "Integrated operations snapshot failed with exit code $LASTEXITCODE." }
