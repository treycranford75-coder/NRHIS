# Calibration Dual-Run Verification Runbook

## Execute against an approved reference case

```powershell
python -m nrhis_calibration.dual_run_cli `
  .\data\calibration-reference-cases\<CASE_ID>\case.json `
  .\reports\dual-run `
  --summary-output .\reports\dual-run-summary.json
```

## Development-only unapproved case

```powershell
python -m nrhis_calibration.dual_run_cli `
  .\data\calibration-reference-cases\<CASE_ID>\case.json `
  .\reports\dual-run `
  --allow-unapproved
```

Do not use `--allow-unapproved` for release evidence.

The command exits with code `0` only when the calibration run succeeds and all
candidate artifacts match the reference case.
