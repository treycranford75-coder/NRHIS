# Build100 — Formal Rincon Evidence Report

Build100 converts the reconciled Build099 Rincon evidence into a formal, reproducible report package. It consumes the latest local `rincon-evidence-*` Build099 analysis directory and creates a Markdown evidence report, a machine-readable findings table, and a SHA-256-bound receipt.

The report intentionally distinguishes direct observations, derived quantities, unobservable discharge periods, and limitations. Negative discharge establishes direction at USGS 08211503; Build100 does not infer the cause, source, or destination of that water. It does not estimate discharge volume during the September–October 2017 outage or after the May 12, 2018 terminal discharge observation.

Build100 also relabels a legacy Build099 timeline field for clarity: the value stored in `mean_reverse_discharge_cfs` on the terminal-discharge row is the final observed discharge value, not a reverse-flow mean. Build100 reports it as `terminal_discharge_cfs` without altering Build099 source evidence.

## Command

```powershell
.\scripts\Generate-Rincon-Evidence-Report.ps1
```

## Outputs

Under `reports/nrhis/rincon-evidence-report-<UTC timestamp>/`:

- `NRHIS_Rincon_Evidence_Report.md`
- `evidence_findings.csv`
- `report-receipt.json`

The workflow is local-only and makes zero USGS requests.
