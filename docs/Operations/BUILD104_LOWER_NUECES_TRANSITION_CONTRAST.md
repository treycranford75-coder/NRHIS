# Build104 - Lower Nueces Upper-Flow Transition Contrast

Build104 corrects the Build103 cumulative-threshold onset artifact. Build103 can
report coherence at the 0th percentile because the full-series Pearson
covariance is dominated by large hydrographs. That result is valid as an
aggregate correlation but is not a defensible event threshold.

Build104 therefore uses disjoint lower-flow and upper-flow subsets at each
candidate percentile threshold (default 60th through 90th percentiles in 5-point
steps). A descriptive upper-flow transition is reported only when:

- upper-subset Pearson r is at least 0.80;
- lower-subset Pearson r is at most 0.50;
- the upper best lag is not 0 or the 72-hour search boundary; and
- upper-subset coherence persists at the next threshold step.

It also writes non-overlapping 20-percentile flow-band correlations so strong
high-flow covariance cannot leak into lower-flow bands, then performs event and
residual analysis only above a resolved transition threshold.

Outputs remain descriptive. No physical travel time, reach water balance, or
causal mechanism is claimed. All analysis is local against the finalized NRHIS
archive and makes zero USGS requests.
