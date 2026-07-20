# NRHIS Build055 Reservoir Harvest Operations

Run from the repository root:

```powershell
.\scripts\Harvest-TWDB-Reservoirs.ps1
```

The harvester retrieves the Corpus Christi municipal reservoir GeoJSON feed from Water Data for Texas and retains only Choke Canyon Reservoir and Lake Corpus Christi. A previous current snapshot is used to calculate storage change when available. The first run reports no change because no prior snapshot exists.

A reservoir observation is marked stale when its source date is older than the configured threshold. The source date is preserved separately from the retrieval time.
