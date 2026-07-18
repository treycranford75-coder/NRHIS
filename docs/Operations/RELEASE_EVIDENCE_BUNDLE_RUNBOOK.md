# Calibration Release Evidence Bundle Runbook

## Create a bundle

```powershell
python -m nrhis_calibration.evidence_cli create `
  .\reports\release-evidence `
  build014-<CASE_ID> `
  .\reports\dual-run-summary.json `
  .\reports\comparison-<CASE_ID>.json `
  --metadata-json '{"release":"v0.1.1-rc14+build014"}'
```

## Validate a bundle

```powershell
python -m nrhis_calibration.evidence_cli validate `
  .\reports\release-evidence\build014-<CASE_ID>\evidence_manifest.json
```

A validation failure blocks release evidence acceptance.
