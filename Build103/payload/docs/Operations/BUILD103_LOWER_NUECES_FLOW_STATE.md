# Build103 Lower Nueces Flow-State Coherence and High-Flow Routing

Build103 follows Build102's key finding that lag-correlation strength changes sharply with flow regime. In the 2017-09-01 through 2018-06-30 analysis, low- and medium-flow optimizer lags were weakly correlated while the high-flow state showed very strong Mathis->Bluntzer, Bluntzer->Calallen, and Mathis->Calallen alignment.

The build scans increasing upstream-discharge percentile thresholds to determine where lag correlation becomes persistently coherent. The default descriptive coherence threshold is Pearson r >= 0.80, with strong coherence at r >= 0.90. A sustained onset requires three consecutive threshold-scan steps and rejects best lags at 0 hours or at the maximum lag-search boundary.

Build103 then analyzes pair-specific coherent-flow events and computes downstream-minus-upstream residual summaries only for coherent-flow conditions. These residuals are not a reach water balance and are not assigned to groundwater, diversions, tributaries, evaporation, regulation, storage, or any other mechanism.

The analysis is local-only, makes zero USGS requests, and does not mutate the finalized historical archive.
