# Calibration Reference Comparison Runbook

## Compare candidate output to an approved case

```powershell
python -m nrhis_calibration.comparison_cli `
  .\data\calibration-reference-cases\<CASE_ID>\case.json `
  .\reports\candidate-run\<RUN_ID>
```

## Export a JSON report

```powershell
python -m nrhis_calibration.comparison_cli `
  .\data\calibration-reference-cases\<CASE_ID>\case.json `
  .\reports\candidate-run\<RUN_ID> `
  --json-output .\reports\comparison-<CASE_ID>.json
```

The command exits with code `0` when all artifacts match and `1` when any
artifact differs.

Use `--allow-unapproved` only for development and never for release evidence.
