# NRHIS Sprint 2 Build095 Release Notes

Build095 adds a bounded-memory local query engine for the finalized 12-million-record USGS historical archive. A compact sparse byte-offset index enables fast evidence-window extraction by date, station, and parameter without contacting USGS or loading the full archive into memory. Every query bundle records source and output hashes for reproducibility.
