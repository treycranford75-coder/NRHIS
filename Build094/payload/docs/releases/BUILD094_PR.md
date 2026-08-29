## NRHIS Sprint 2 - Build094

### Large-archive finalization and disk-backed identity index

- replaces the final all-records-in-memory CSV sort with a bounded-memory external merge sort;
- adds a persistent SQLite identity index so future historical updates do not keep millions of compound identities in RAM;
- adds a finalize-only recovery path that validates the completed checkpoint and makes **zero USGS requests**;
- records SHA-256 hashes and byte sizes for the completed JSONL and CSV in the finalization receipt;
- preserves global CSV ordering by observation time, station, and parameter;
- leaves the already-recovered raw USGS evidence and normalized JSONL untouched.

The production checkpoint already shows `completed_through = 2026-08-29`, so Build094 is a finalization/reliability build, not a data reacquisition build.
