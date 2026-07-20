[CmdletBinding()]
param([string]$RepositoryRoot = "C:\GitHub\NRHIS")
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path $RepositoryRoot).Path
$config = Get-Content (Join-Path $repo "config\nrhis\operations_schedule.json") -Raw | ConvertFrom-Json
$rows = foreach ($slot in @("Morning", "Evening")) {
    $name = "$($config.task_prefix) - $slot"
    $task = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
    $info = if ($task) { Get-ScheduledTaskInfo -TaskName $name } else { $null }
    [pscustomobject]@{
        TaskName = $name
        Installed = [bool]$task
        State = if ($task) { [string]$task.State } else { "Missing" }
        LastRunTime = if ($info) { $info.LastRunTime } else { $null }
        LastTaskResult = if ($info) { $info.LastTaskResult } else { $null }
        NextRunTime = if ($info) { $info.NextRunTime } else { $null }
    }
}
$rows | Format-Table -AutoSize
