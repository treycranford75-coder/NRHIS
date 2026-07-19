## NRHIS Sprint 2 — Build052

Build052 turns the historical USGS backfill into an operational incremental update process.

### Included

- Resume from the newest stored observation with a configurable overlap
- Duplicate-safe updates through the selected end date
- Missing and stale station/parameter detection
- Observation-gap detection
- Basin data-quality JSON and CSV outputs
- Machine-readable incremental update receipt

### Controls retained

- Merge target remains `develop`
- No-prune synchronization
- Workflow-contract and CI-parity gates
- Pre-release publication, verification, archival, and next-build chaining

Build051 remains complete, published, verified, and archived.
