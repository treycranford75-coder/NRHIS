## NRHIS Sprint 2 — Build066

Build066 adds scheduler health monitoring and missed-run detection for the twice-daily NRHIS operations schedule.

### Included
- Confirms Morning and Evening Windows tasks exist.
- Verifies each task is Ready or Running.
- Checks the latest operations-cycle status.
- Checks the latest scheduler-run receipt and exit code.
- Writes JSON, CSV, and receipt outputs.
- Supports `-FailOnUnhealthy` for automation.

Build065 remains complete, published, verified, and archived.
