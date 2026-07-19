## NRHIS Sprint 2 — Build050

Build050 delivers the first production Nueces–Frio basin USGS harvest capability.

### Included

- live USGS Instantaneous Values client using the Python standard library;
- six-station basin configuration;
- discharge, gage height, temperature, and conductance normalization;
- duplicate-safe history and raw-response archival;
- stale/provisional/missing validation;
- current JSON/CSV, station-status CSV, and run receipts;
- deterministic fixture tests for parsing, TDS estimation, and rerun deduplication.

### Controls retained

- `develop` merge target;
- pre-push workflow and CI parity gates;
- no-prune synchronization;
- pre-release publication and verified completion evidence;
- protected repository location outside OneDrive.
