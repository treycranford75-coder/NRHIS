# Build102 Lower Nueces Lag Stability and Reach Residuals

Build102 extends the Build101 Mathis-Bluntzer-Calallen discharge network with stability tests rather than treating a single best correlation lag as a precise travel time.

Outputs include overall near-peak lag windows, monthly lag estimates, rolling 30-day and 60-day lag estimates, upstream-discharge-tercile lag estimates, lag-adjusted hourly residuals, and reach residual summaries.

The near-peak windows use two descriptive thresholds: lags whose Pearson correlation is within 0.0005 of the pair-specific maximum, and lags within 0.001 of that maximum. Build102 also compares the sum of the two shorter-reach near-peak windows with the direct Mathis-to-Calallen near-peak window.

Lag-adjusted residuals are downstream hourly mean discharge at t+lag minus upstream hourly mean discharge at t. They are not a reach water balance and are not attributed to groundwater, diversions, evaporation, tributaries, or any other mechanism without independent evidence.

The analysis is local-only, makes zero USGS requests, and does not mutate the finalized historical archive.
