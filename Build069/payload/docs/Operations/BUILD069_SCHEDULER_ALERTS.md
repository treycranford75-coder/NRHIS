# Build069 Scheduler Alert Artifacts

Build069 converts the machine-readable scheduler health result into operational alert artifacts.

Outputs:

- `data/nrhis/scheduler/scheduler_alert.json`
- `data/nrhis/scheduler/scheduler_alert.md`
- `data/nrhis/scheduler/scheduler_alert_history.jsonl`
- `data/nrhis/receipts/scheduler_alert_receipt.json`

Severity rules:

- `info`: no active problems
- `warning`: noncritical health degradation such as a stale receipt
- `critical`: missing or invalid evidence, failed scheduler execution, failed operations cycle, or a missed schedule slot

Use `-FailOnAlert` when the alert should return a nonzero exit code for any active problem.
