# NRHIS Sprint 2 Build090 Release Notes

Build090 fixes a deep-history USGS backfill resume defect: a checkpoint from a newer study window can no longer cause an older requested period to be silently skipped. It also adds a dedicated long-range historical bootstrap command for the Nueces basin, while preserving raw API evidence, duplicate-safe normalized history, resumable chunking, CSV rebuilds, and run receipts.
