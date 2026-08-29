# Build090 - Deep-History USGS Bootstrap

Build090 closes a historical-backfill resume defect and adds an operator command for building the long NRHIS USGS archive.

## Why this build matters

The Build052 backfill stored one global `data/nrhis/backfill/checkpoint.json`. If that checkpoint had already advanced through a recent-range run (for example, a run beginning in 2024), a later request beginning years earlier could inherit the newer `completed_through` value and silently skip the older period.

Build090 makes checkpoint reuse scope-aware. A checkpoint is reused only when its `requested_start` matches the requested start date. A deeper-history request therefore starts at the requested older date while preserving the append-only, duplicate-safe normalized archive.

## Full archive bootstrap

From the repository root:

```powershell
.\scripts\Bootstrap-USGS-History.ps1
```

Default range: `2007-01-01` through today, seven-day USGS request chunks, using the existing `config/nrhis/usgs_nueces_basin.json` station registry.

Preview the workload without making requests:

```powershell
.\scripts\Bootstrap-USGS-History.ps1 -PlanOnly
```

Custom range:

```powershell
.\scripts\Bootstrap-USGS-History.ps1 -StartDate "2006-01-01" -EndDate "2026-08-29"
```

The underlying Build052 engine remains restart-safe and duplicate-safe. Raw responses, normalized JSONL/CSV, checkpoints, and run receipts remain under `data/nrhis`.
