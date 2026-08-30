## Build104 - Lower Nueces upper-flow transition contrast

Build104 supersedes Build103 `coherence_onset` as an event-threshold estimator.
It compares disjoint lower/upper flow subsets, requires weak lower-flow and
coherent upper-flow behavior, checks persistence across thresholds, and adds
non-overlapping flow-band diagnostics. Event and residual analysis is performed
only when a contrast threshold is resolved.

The analysis remains local-only, makes zero USGS requests, and explicitly avoids
physical travel-time, water-balance, or causal claims.
