## Build067: align scheduler receipts and health monitoring

This build permanently incorporates the field-validated fixes from Build066:

- scheduled-cycle wrapper writes `data/nrhis/scheduler/latest_scheduler_run.json`;
- config uses the exact `scheduler_receipt` key consumed by the health checker;
- JSON receipts are written UTF-8 without BOM;
- health checker tolerates historical UTF-8 BOM files;
- successful receipt schema (`status=completed`, `exit_code=0`) produces a healthy result.
