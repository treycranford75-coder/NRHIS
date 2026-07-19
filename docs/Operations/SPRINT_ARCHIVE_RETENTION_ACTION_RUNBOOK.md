# Sprint Archive Retention Action Runbook

Create a dry-run action manifest:

```powershell
python -m nrhis_calibration.archive_retention_action_cli create `
  .\reports\sprint-archive-retention.json `
  .\reports\sprint-archive-retention-approval.json `
  .\reports\sprint-archive-retention-actions.json
```

Validate it:

```powershell
python -m nrhis_calibration.archive_retention_action_cli validate `
  .\reports\sprint-archive-retention.json `
  .\reports\sprint-archive-retention-approval.json `
  .\reports\sprint-archive-retention-actions.json
```

This workflow does not change archive files.
