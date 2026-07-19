# Build051 USGS Historical Backfill

Build051 adds restart-safe, chunked historical extraction from the USGS Instantaneous Values service for the configured Nueces-Frio basin stations.

## Default study period

The operational wrapper defaults to February 1, 2024 through the current date, matching the Vacate the Order baseline study period.

## Run

```powershell
.\scripts\Backfill-USGS-History.ps1
```

Optional date window:

```powershell
.\scripts\Backfill-USGS-History.ps1 -StartDate "2024-02-01" -EndDate "2024-03-31" -ChunkDays 7
```

## Outputs

- raw response archive per date chunk;
- append-only duplicate-safe historical JSONL;
- rebuilt historical CSV;
- resumable checkpoint;
- run receipt with chunk hashes and counts.

Estimated TDS remains explicitly labeled and is calculated as `specific conductance × 0.65`.
