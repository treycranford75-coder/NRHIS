[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$RepositoryRoot = "C:\GitHub\NRHIS",
    [string]$ConfigPath,
    [switch]$Replace,
    [switch]$RunAsSystem
)
$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest
$repo = (Resolve-Path $RepositoryRoot).Path
if (-not $ConfigPath) { $ConfigPath = Join-Path $repo "config\nrhis\operations_schedule.json" }
$config = Get-Content $ConfigPath -Raw | ConvertFrom-Json
$runner = Join-Path $repo "scripts\Run-NrhisScheduledCycle.ps1"
if (-not (Test-Path $runner -PathType Leaf)) { throw "Scheduled-cycle runner not found: $runner" }
$principal = if ($RunAsSystem) {
    New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
} else {
    New-ScheduledTaskPrincipal -UserId $env:USERNAME -LogonType Interactive -RunLevel Highest
}
$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit (New-TimeSpan -Minutes ([int]$config.execution_time_limit_minutes)) `
    -StartWhenAvailable:([bool]$config.start_when_available) `
    -AllowStartIfOnBatteries:([bool]$config.allow_on_battery) `
    -DontStopIfGoingOnBatteries:([bool]$config.allow_on_battery)
foreach ($slot in @("morning", "evening")) {
    $entry = $config.$slot
    if (-not [bool]$entry.enabled) { continue }
    $taskName = "$($config.task_prefix) - $($slot.Substring(0,1).ToUpper()+$slot.Substring(1))"
    $arguments = @(
        "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", ('"{0}"' -f $runner),
        "-RepositoryRoot", ('"{0}"' -f $repo), "-ScheduleSlot", $slot,
        "-QaPassesCompleted", ([string]$config.qa_passes_completed)
    ) -join " "
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $arguments -WorkingDirectory $repo
    $at = [datetime]::ParseExact([string]$entry.time, "HH:mm", $null)
    $trigger = New-ScheduledTaskTrigger -Daily -At $at
    if ($Replace) { Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue }
    if ((Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue) -and -not $Replace) {
        throw "Scheduled task already exists: $taskName. Use -Replace to update it."
    }
    if ($PSCmdlet.ShouldProcess($taskName, "Register NRHIS scheduled task")) {
        Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "NRHIS $slot operations cycle installed by Build064" | Out-Null
        Write-Host "Installed: $taskName at $($entry.time)" -ForegroundColor Green
    }
}
