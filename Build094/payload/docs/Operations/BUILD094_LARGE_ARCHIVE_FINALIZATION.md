# Build094 Large-Archive Finalization

Build094 closes the production-scale memory failure exposed only after the 2007-01-01 through 2026-08-29 USGS acquisition had already reached its final chunk.

The completed checkpoint is authoritative evidence that acquisition finished through 2026-08-29. Build094 therefore does not redownload that history. It adds a finalize-only path that validates the completed checkpoint, builds a disk-backed SQLite identity index by streaming the append-only JSONL, creates the globally time-sorted CSV using an external merge sort with bounded memory, hashes the JSONL and CSV, and writes a finalization receipt.

The normal historical backfill path is also moved from the multi-million-entry in-memory identity set to the same disk-backed SQLite identity index. This keeps future incremental updates restart-safe without RAM usage growing with the archive.

Operational recovery after Build094:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File ".\scripts\Finalize-USGS-History.ps1" `
  -StartDate "2007-01-01" `
  -EndDate "2026-08-29"
```

The finalizer makes zero USGS requests.
