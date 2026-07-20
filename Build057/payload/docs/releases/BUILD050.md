# NRHIS Sprint 2 Build050 — Production USGS Basin Harvest

Build050 returns Sprint 2 to hydrologic functionality by delivering a production USGS Instantaneous Values harvest for six Nueces–Frio basin stations.

## Functional scope

- live USGS IV request for discharge, gage height, water temperature, and specific conductance;
- Cotulla, Tilden, Three Rivers, Mathis, Bluntzer, and Calallen station configuration;
- raw response archive and SHA-256 receipt evidence;
- normalized latest observations with source timestamps and qualifiers;
- stale, provisional, missing-site, and invalid-value handling;
- duplicate-safe append-only history;
- current-condition JSON/CSV and station-status CSV;
- estimated TDS from conductance at the locked NRHIS factor of 0.65.

Release automation remains frozen except where required to ship and verify the functional build.
