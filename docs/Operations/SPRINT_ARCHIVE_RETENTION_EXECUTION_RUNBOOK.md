# Sprint Archive Retention Execution Runbook

Simulate execution:

```powershell
python -m nrhis_calibration.archive_retention_execution_cli simulate `
  .\reports\sprint-archive-retention.json `
  .\reports\sprint-archive-retention-approval.json `
  .\reports\sprint-archive-retention-actions.json `
  .\reports\sprint-archive-retention-execution.json
```

Validate the report:

```powershell
python -m nrhis_calibration.archive_retention_execution_cli validate `
  .\reports\sprint-archive-retention-execution.json
```

This workflow is simulation-only and does not change archive files.
