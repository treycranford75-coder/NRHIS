# Build050 Production USGS Basin Harvest

Run from the protected repository root:

```powershell
.\scripts\Harvest-USGS-Production.ps1
```

Operational products are written under `data/nrhis`:

- immutable raw USGS API responses;
- duplicate-safe normalized JSONL history;
- current-condition JSON and CSV;
- station-status CSV with missing, stale, and provisional counts;
- machine-readable harvest receipts.

Specific conductance parameter `00095` is converted to an estimated TDS value using `0.65 × specific conductance`. The result is explicitly stored as an estimate and never replaces the source conductance observation.
