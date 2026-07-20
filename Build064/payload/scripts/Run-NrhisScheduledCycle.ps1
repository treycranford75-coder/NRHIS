[CmdletBinding()]
param(
    [string]$RepositoryRoot = "C:\GitHub\NRHIS",
    [ValidateSet("morning", "evening", "manual")][string]$ScheduleSlot = "manual",
    [ValidateRange(0,2)][int]$QaPassesCompleted = 0
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$repo = (Resolve-Path $RepositoryRoot).Path
Set-Location $repo
$logs = Join-Path $repo "data\nrhis\scheduler_logs"
New-Item -ItemType Directory -Path $logs -Force | Out-Null
$stamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssZ")
$cycleName = "{0}-{1}" -f (Get-Date -Format "yyyy-MM-dd"), $ScheduleSlot
$log = Join-Path $logs ("{0}-{1}.log" -f $cycleName, $stamp)
$latest = Join-Path $logs ("latest-{0}.json" -f $ScheduleSlot)
$runner = Join-Path $repo "scripts\Run-NrhisOperationsCycle.ps1"
$started = [DateTime]::UtcNow
$status = "failed"
$exitCode = 1
try {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File $runner -QaPassesCompleted $QaPassesCompleted -CycleName $cycleName *>&1 | Tee-Object -FilePath $log
    $exitCode = $LASTEXITCODE
    if ($exitCode -eq 0) { $status = "completed" }
} finally {
    $receipt = [ordered]@{
        schema_version = 1
        build = "064"
        schedule_slot = $ScheduleSlot
        cycle_name = $cycleName
        started_at = $started.ToString("o")
        completed_at = [DateTime]::UtcNow.ToString("o")
        status = $status
        exit_code = $exitCode
        qa_passes_completed = $QaPassesCompleted
        log_path = $log
    }
    $receipt | ConvertTo-Json -Depth 5 | Set-Content $latest -Encoding utf8
}
if ($exitCode -ne 0) { throw "Scheduled NRHIS cycle failed with exit code $exitCode. See $log" }
