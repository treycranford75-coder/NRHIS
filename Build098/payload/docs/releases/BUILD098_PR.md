## Build098: Rincon reverse-flow volume integration

This build extends the Build097 Rincon discontinuity analysis with evidence-grade reverse-flow volume integration from the finalized local USGS archive.

### Adds
- piecewise-linear integration of negative discharge, including exact linear zero-crossing treatment;
- no interpolation across gaps longer than two observation cadences;
- reverse-flow interval volume, duration, mean reverse discharge, and minimum discharge;
- duration-class summaries;
- monthly reverse-flow summaries;
- phase summaries for pre-gap, 2017 discharge gap, post-gap/pre-terminal, and post-terminal periods;
- explicit `not_observable_from_discharge` status for the gap and post-terminal phases rather than imputing missing flow;
- SHA-256-bound evidence outputs and receipt.

### Safety
- local finalized archive only;
- zero USGS requests;
- no modification of the 12,061,104-record finalized historical archive.
