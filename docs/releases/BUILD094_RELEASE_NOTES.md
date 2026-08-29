# NRHIS Sprint 2 Build094 Release Notes

Build094 makes the completed deep-history archive safe to finalize at production scale. It removes the unbounded in-memory CSV rebuild that caused the post-acquisition memory error, adds a disk-backed SQLite identity index for future refreshes, and adds an explicit finalize-only command that makes no USGS requests. Finalization writes a globally sorted CSV and a receipt containing file sizes and SHA-256 hashes for the JSONL and CSV.
