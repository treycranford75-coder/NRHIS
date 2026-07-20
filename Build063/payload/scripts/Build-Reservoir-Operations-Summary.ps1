[CmdletBinding()]
param(
    [string]$Config = "config/nrhis/reservoir_operations_summary.json",
    [string]$DataRoot = "data/nrhis"
)
$ErrorActionPreference = "Stop"
python .\scripts\build_reservoir_operations_summary.py --config $Config --data-root $DataRoot
if ($LASTEXITCODE -ne 0) { throw "Reservoir operations summary failed with exit code $LASTEXITCODE" }
