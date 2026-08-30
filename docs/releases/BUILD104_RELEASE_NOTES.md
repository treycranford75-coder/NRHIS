Build104 corrects the lower Nueces coherence-onset artifact identified after
Build103 production analysis. A cumulative exceedance subset can remain strongly
correlated even at the 0th percentile because large hydrographs dominate
covariance; that does not define a meaningful high-flow event threshold.

Build104 replaces that threshold logic with disjoint lower-versus-upper flow
contrast scanning over the upper portion of the discharge distribution. It also
adds non-overlapping percentile-band coherence checks, transition-qualified
upper-flow event lags, and transition-qualified residual summaries. Build103
remains preserved as part of the audit trail, but its 0th-percentile onset values
must not be used as event thresholds.

All results are descriptive, use the finalized local NRHIS archive, and make zero
USGS requests.
