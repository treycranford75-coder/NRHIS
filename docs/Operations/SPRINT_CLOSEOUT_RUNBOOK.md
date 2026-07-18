# Sprint Closeout Runbook

Prepare a JSON array containing one object for each release candidate, then run:

```powershell
python -m nrhis_calibration.sprint_closeout_cli `
  .\reports\sprint2-release-inventory.json `
  --sprint "Sprint 2" `
  --first-build 1 `
  --final-build 16 `
  --minimum-coverage 80 `
  --json-output .\reports\sprint2-closeout.json
```

The command exits with code `0` only when every closeout check passes.
