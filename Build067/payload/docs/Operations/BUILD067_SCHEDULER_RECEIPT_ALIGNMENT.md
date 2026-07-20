# Build067 — Scheduler Receipt Alignment

Build067 permanently aligns the scheduled-cycle writer and scheduler-health reader on the canonical path `data/nrhis/scheduler/latest_scheduler_run.json`.

It also writes JSON as UTF-8 without BOM and reads JSON with `utf-8-sig` tolerance for backward compatibility.
