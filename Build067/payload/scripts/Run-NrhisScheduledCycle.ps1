[CmdletBinding()]
param(
    [string]$RepositoryRoot = (Get-Location).Path,
    [ValidateSet('morning','evening','manual')]
    [string]$ScheduleSlot = 'manual',
    [ValidateRange(0,2)]
    [int]$QaPassesCompleted = 0
)
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
$repo = (Resolve-Path $RepositoryRoot).Path
Set-Location $repo
$logs = Join-Path $repo 'data\nrhis\scheduler_logs'
New-Item -ItemType Directory -Path $logs -Force | Out-Null
$stamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssZ')
$cycleName = '{0}-{1}' -f (Get-Date -Format 'yyyy-MM-dd'), $ScheduleSlot
$log = Join-Path $logs ('{0}-{1}.log' -f $cycleName, $stamp)
$slotLatest = Join-Path $logs ('latest-{0}.json' -f $ScheduleSlot)
$started = [DateTime]::UtcNow
$exitCode = 1
$status = 'failed'
try {
    & powershell.exe `
        -NoProfile `
        -NonInteractive `
        -ExecutionPolicy Bypass `
        -File (Join-Path $repo "scripts\Run-NrhisOperationsCycle.ps1") `
        -QaPassesCompleted $QaPassesCompleted `
        -CycleName $cycleName `
        2>&1 |
        Tee-Object -FilePath $log
    $exitCode = $LASTEXITCODE
    if ($exitCode -eq 0) { $status = 'completed' }
}
finally {
    $receipt = [ordered]@{
        schema_version = 1
        build = '067'
        schedule_slot = $ScheduleSlot
        cycle_name = $cycleName
        started_at = $started.ToString('o')
        completed_at = [DateTime]::UtcNow.ToString('o')
        status = $status
        exit_code = $exitCode
        qa_passes_completed = $QaPassesCompleted
        log_path = $log
    }
    $receiptJson = $receipt | ConvertTo-Json -Depth 5
    [System.IO.File]::WriteAllText($slotLatest, $receiptJson + "`n", [System.Text.UTF8Encoding]::new($false))
    $schedulerRoot = Join-Path $repo 'data\nrhis\scheduler'
    New-Item -ItemType Directory -Path $schedulerRoot -Force | Out-Null
    $canonicalLatest = Join-Path $schedulerRoot 'latest_scheduler_run.json'
    [System.IO.File]::WriteAllText($canonicalLatest, $receiptJson + "`n", [System.Text.UTF8Encoding]::new($false))
}
if ($exitCode -ne 0) { throw "Scheduled NRHIS cycle failed with exit code $exitCode. See $log" }
