## NRHIS Sprint 2 - Build090

Build090 makes the USGS historical backfill safe for deep-history bootstrap.

### Included

- scope-aware historical backfill checkpoint reuse;
- protection against a 2024+ checkpoint skipping a newly requested 2007+ archive;
- explicit receipt fields showing whether a checkpoint was used or ignored;
- `scripts/Bootstrap-USGS-History.ps1` for long-range basin extraction;
- `-PlanOnly` workload preview;
- deterministic regression tests with no live-network dependency.

### Hydrologic intent

This build returns development to the core NRHIS mission: recovering and preserving long-duration Nueces River basin observations for station-to-station analysis and reproducible historical research.
