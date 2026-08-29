# Build095: add finalized historical archive query engine

## Summary

- adds a sparse byte-offset index over the globally sorted finalized USGS CSV;
- enables fast local date/station/parameter evidence-window queries without network access;
- binds each query receipt to the finalized source CSV SHA-256 and query-index SHA-256;
- writes compact evidence bundles under `data/nrhis/queries/`;
- validates chronological CSV ordering when the sparse index is built;
- keeps memory usage bounded regardless of the 12-million-record archive size.

## Validation

Build095 includes deterministic tests for indexing, filtering, chronological-order
validation, source-change detection, and network-free evidence receipts.
