$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot
if (-not (Test-Path ".venv")) { py -m venv .venv }
$python = ".\.venv\Scripts\python.exe"
& $python -m pip install --disable-pip-version-check pandas numpy requests
& $python .\calibrate_pass1.py --start-wy 2008 --end-wy 2026 --out pass1_output
Write-Host "Complete. ZIP and upload the pass1_output folder to ChatGPT."
Read-Host "Press Enter to close"
