## NRHIS Sprint 2 - Build069

Build069 converts scheduler-health results into alert artifacts for operations review and downstream notification workflows.

### Included

- JSON and Markdown scheduler alerts
- severity classification: info, warning, critical
- append-only JSONL alert history with duplicate suppression
- machine-readable completion receipt
- optional nonzero exit through `-FailOnAlert`
- deterministic tests for clear, stale, missed-slot, and history behavior
