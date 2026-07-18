# ES-002 Harvest Provenance Standard

1. Every authoritative download is preserved before normalization.
2. A harvest run receives a UTC run identifier in `YYYYMMDDTHHMMSSZ` form.
3. Raw source values are never overwritten or silently corrected.
4. Normalized records retain station, parameter, unit, timestamp, qualifier, and source fields.
5. Metadata records the endpoint, resolved request URL, query, registry hash, artifact hashes,
   date coverage, and record counts.
6. Generated source and normalized artifacts are excluded from routine source-control commits.
7. Network and schema failures produce a nonzero exit and an operational log entry.
