[CmdletBinding()]
param([string]$ReportDate)
$repo = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
Set-Location $repo
$argsList = @('scripts/reservoir_water_budget.py')
if ($ReportDate) { $argsList += @('--date',$ReportDate) }
python @argsList
if ($LASTEXITCODE -ne 0) { throw "Reservoir water budget failed with exit code $LASTEXITCODE" }
