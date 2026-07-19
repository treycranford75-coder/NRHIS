## NRHIS Sprint 2 — Build051

Build051 extends the production USGS harvest engine into historical and incremental basin backfill.

### Included

- Explicit start/end date extraction
- Seven-day chunking by default
- February 2024 study-period default
- Restart-safe checkpointing
- Duplicate-safe append-only JSONL
- Rebuilt basin-wide CSV
- Raw response archive and SHA-256 evidence
- Chunk-level and run-level receipts
- Estimated TDS retained as a clearly labeled estimate

### Controls retained

- `develop` merge target
- No-prune synchronization
- Workflow contract and CI parity gates
- Pre-release publication and verification
- Installer archival and next-build chaining
