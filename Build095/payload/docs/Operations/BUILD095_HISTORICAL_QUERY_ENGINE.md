# Build095 — Historical Query Engine

Build095 turns the finalized 2007–2026 USGS archive into a fast local evidence source.

## Design

The finalized CSV is globally sorted by `observed_at`, but it is too large to scan from
its first byte for every question. Build095 creates a small sparse byte-offset index over
the CSV. The default stride is 50,000 observations, so a 12-million-row archive needs only
about 242 seek points. Queries binary-search those seek points, jump near the requested
start time, and scan only the requested date window.

The index-building pass also calculates SHA-256 for the exact finalized CSV and rejects a
CSV whose timestamps regress. Every query bundle records the source CSV hash, index hash,
filters, result count, and output hash. No query operation contacts USGS.

## First query

```powershell
.\scripts\Query-USGS-History.ps1 `
  -StartDate "2018-04-01" `
  -EndDate "2018-06-30" `
  -SiteNo "08211503" `
  -ParameterCode "00060","00065"
```

The first query creates `data/nrhis/backfill/usgs_history_query_index.json`. Later queries
reuse it as long as the finalized CSV byte size is unchanged.

Query bundles are written under `data/nrhis/queries/query-<UTC timestamp>/` with:

- `observations.csv`
- `query-receipt.json`

Date-only end values are inclusive. Explicit ISO timestamps are treated as exclusive end
boundaries.
