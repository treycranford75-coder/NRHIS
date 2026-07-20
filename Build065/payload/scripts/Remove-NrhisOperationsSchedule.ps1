[CmdletBinding(SupportsShouldProcess, ConfirmImpact="High")]
param([string]$TaskPrefix = "NRHIS Operations")
$ErrorActionPreference = "Stop"
foreach ($slot in @("Morning", "Evening")) {
    $name = "$TaskPrefix - $slot"
    if (Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue) {
        if ($PSCmdlet.ShouldProcess($name, "Unregister scheduled task")) {
            Unregister-ScheduledTask -TaskName $name -Confirm:$false
            Write-Host "Removed: $name" -ForegroundColor Green
        }
    }
}
