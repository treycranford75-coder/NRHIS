# Build097 - Rincon Discontinuity and Directional-Flow Analysis

Build097 is the first analytical NRHIS build operating on the finalized local USGS archive.
It does not call USGS and does not modify the historical archive.

## Purpose

The analyzer converts previously manual Rincon Bayou checks into a repeatable evidence workflow for USGS station 08211503. It identifies:

- material gaps in published discharge (00060);
- whether gage height (00065) continued during each discharge gap;
- the last published discharge observation and whether stage continued afterward;
- contiguous negative-flow intervals and their duration, minimum, and mean discharge.

## Evidence outputs

Each run writes a timestamped directory beneath `data/nrhis/analysis` containing:

- `discharge_gaps.csv`
- `negative_flow_intervals.csv`
- `rincon_flow_summary.json`
- `analysis-receipt.json`

The receipt binds the outputs to the finalized historical CSV and sparse query index by SHA-256 and records `network_requests_made: 0`.

## Default analysis

```powershell
.\scripts\Analyze-Rincon-Flow.ps1
```

Defaults:

- site 08211503;
- 2007-01-01 through 2026-08-29;
- 15-minute expected cadence;
- discharge gaps of at least 24 hours;
- stage continuity threshold of 80 percent of missing discharge slots.

The thresholds can be overridden for event-scale review.
