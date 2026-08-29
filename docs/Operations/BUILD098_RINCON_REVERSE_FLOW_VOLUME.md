# Build098 - Rincon Reverse-Flow Volume Analysis

Build098 adds evidence-grade integration of negative discharge at USGS 08211503 using only the finalized local NRHIS archive.

## Method

For each pair of consecutive valid discharge observations, the workflow assumes a straight line between the instantaneous measurements. If both values are negative, the trapezoidal negative area is integrated. If the segment crosses zero, the zero-crossing time is solved analytically and only the negative triangular portion is integrated. No interpolation is performed when the interval between observations exceeds twice the configured cadence (30 minutes at the default 15-minute cadence).

Integrated flow is converted from cubic-foot-seconds to acre-feet using 43,560 cubic feet per acre-foot.

## Evidence safeguards

- Local finalized archive only; zero USGS requests.
- No discharge volume is imputed across material discharge gaps.
- No discharge volume is imputed after the terminal discharge observation.
- Gap and post-terminal phases are explicitly marked `not_observable_from_discharge`.
- Stage counts are retained for those phases to distinguish discharge-data absence from total station-data absence.
- All output tables and the summary are SHA-256 bound to the finalized source CSV and sparse query index.

## Outputs

Each run writes a timestamped directory under `data/nrhis/analysis` containing:

- `reverse_flow_intervals.csv`
- `duration_classes.csv`
- `monthly_reverse_flow.csv`
- `phase_summary.csv`
- `rincon_reverse_flow_summary.json`
- `analysis-receipt.json`

The intended first production window is 2017-09-01 through 2018-06-30, spanning the 47-day 2017 discharge outage and the May 12, 2018 terminal discharge discontinuity.
