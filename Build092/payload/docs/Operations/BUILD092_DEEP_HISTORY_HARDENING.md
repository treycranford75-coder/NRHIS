# Build092 - USGS Deep-History Evidence and Scale Hardening

Build090 made a 2007-present historical bootstrap safe from a newer-range checkpoint. The Build090 PlanOnly run then exposed a long-run readiness gap: the configured network contained only six stations and omitted the two Rincon Bayou USGS records central to lower-Nueces/delta analysis.

Build092 hardens the archive before the first multi-year production run.

## Network coverage

Adds:

- USGS 08211503 - Rincon Bayou Channel near Calallen, TX
- USGS 0821150305 - Rincon Bayou Channel near Odem, TX

The latter has long-running temperature and specific-conductance observations; USGS 08211503 preserves the historical directional-flow/stage record used in prior Nueces Delta work.

## Scale behavior

The historical JSONL identity set is now loaded once at the beginning of a run and updated in memory as chunks are appended. The previous implementation rescanned the entire growing JSONL file for every chunk, which becomes increasingly expensive during a roughly 19-year, 7-day-chunk bootstrap.

## Evidence integrity

Raw USGS response bytes are now written exactly as received. The SHA-256 recorded in each chunk receipt therefore hashes the preserved evidence file itself. If the same date-range path already exists with different bytes, the earlier file is retained and the differing response is written to a hash-suffixed filename rather than overwriting evidence.

## Operational rule

Build092 itself makes no production USGS history requests. After merge, rerun `Bootstrap-USGS-History.ps1 -PlanOnly`; if the registry is correct, launch the production bootstrap as a separate operational step.
