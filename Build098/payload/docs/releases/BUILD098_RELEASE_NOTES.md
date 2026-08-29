# NRHIS Sprint 2 Build098 Release Notes

Build098 converts the Build097 directional-flow findings into evidence-grade reverse-flow volume analysis. It integrates the negative portion of the original 15-minute discharge record using piecewise-linear interpolation, solves zero crossings analytically, refuses to interpolate across material observation gaps, and reports reverse-flow interval, duration-class, monthly, and phase summaries.

The workflow explicitly marks the 2017 discharge outage and the post-May-12-2018 terminal period as not observable from discharge rather than estimating missing volumes. All outputs are SHA-256 bound to the finalized local archive and sparse query index, and the workflow makes zero USGS requests.
