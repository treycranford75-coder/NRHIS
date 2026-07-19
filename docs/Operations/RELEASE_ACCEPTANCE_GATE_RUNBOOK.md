# Calibration Release Acceptance Gate Runbook

## Evaluate a release bundle

```powershell
python -m nrhis_calibration.release_gate_cli `
  v0.1.1-rc15+build015 `
  .\reports\release-evidence\<BUNDLE_ID>\evidence_manifest.json `
  --json-output .\reports\release-gate-build015.json
```

The command exits with code `0` only when every required gate passes.

## Development-only mismatch override

```powershell
python -m nrhis_calibration.release_gate_cli `
  development-check `
  .\reports\release-evidence\<BUNDLE_ID>\evidence_manifest.json `
  --allow-mismatch
```

Do not use `--allow-mismatch` for production release evidence.
