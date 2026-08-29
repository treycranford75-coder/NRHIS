# Build098

Build098 adds evidence-grade Rincon Bayou reverse-flow volume integration to the NRHIS analytical layer.

It integrates the negative portion of the original instantaneous discharge series using piecewise-linear interpolation, refuses to bridge material data gaps, classifies reverse-flow intervals by duration, summarizes monthly reverse-flow volume, and separates observable phases from the 2017 discharge gap and post-May-2018 terminal period where discharge volume cannot be measured.

The workflow is local-only and makes zero USGS requests.
