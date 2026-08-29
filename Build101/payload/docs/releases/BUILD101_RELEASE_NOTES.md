# NRHIS Sprint 2 Build101 Release Notes

Build101 starts the lower-Nueces main-stem analytical phase. It uses the finalized local NRHIS USGS archive to analyze discharge at Mathis (08211000), Bluntzer (08211200), and Calallen (08211500), with no network requests and no archive mutation.

The build creates hourly discharge evidence, daily station summaries, complete pairwise lag-correlation tables from 0 through a configurable maximum lag, and a best-lag table for Mathis→Bluntzer, Bluntzer→Calallen, and Mathis→Calallen. Positive lag means downstream observations are compared later than the upstream observations.

These lag results are deliberately descriptive. NRHIS does not equate the strongest statistical alignment with physical water-particle travel time or causation. Reservoir operations, diversions, tributary inflows, local gains/losses, backwater, regulation, and missing observations remain potential influences.
