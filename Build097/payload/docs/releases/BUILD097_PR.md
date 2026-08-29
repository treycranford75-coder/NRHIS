## Build097 - Rincon Discontinuity and Directional-Flow Analysis

This build adds the first analytical workflow over the finalized NRHIS historical USGS archive.

### Adds
- bounded-memory analysis for USGS 08211503;
- material discharge-gap detection;
- stage-continuity measurement across discharge gaps;
- terminal discharge-versus-stage monitoring comparison;
- negative-flow interval summaries;
- evidence CSV/JSON outputs with SHA-256 provenance receipts;
- local-only PowerShell and Python CLIs.

### Safety
- zero USGS requests;
- no changes to the finalized historical archive;
- uses the Build095 sparse local query index;
- deterministic synthetic tests cover gap, stage, terminal, and negative-flow behavior.
