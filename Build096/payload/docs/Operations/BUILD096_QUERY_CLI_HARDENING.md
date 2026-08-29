# Build096 Query CLI Hardening

Build096 hardens the local finalized-history query CLI without changing the historical archive.

- `scripts/query_usgs_history.py` bootstraps the repository `src` directory before importing `nrhis_analysis`, so direct execution works without requiring an editable package install.
- `scripts/Query-USGS-History.ps1` normalizes `SiteNo` and `ParameterCode` values after PowerShell parameter binding. This handles the `powershell.exe -File` boundary, where a string array can arrive as one comma-delimited value.
- The wrapper uses dedicated normalized arrays rather than mutating typed input parameters.
- No USGS requests are added and no finalized CSV, JSONL, SQLite identity index, sparse query index, or query evidence bundle is modified by the build.

Observed validation before Build096: the repaired Build095 query returned 12,377 records for site 08211503, parameters 00060 and 00065, for 2018-04-01 through 2018-06-30, with `network_requests_made = 0`.
