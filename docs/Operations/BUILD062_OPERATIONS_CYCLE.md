# Build062 — Twice-Daily Operations Cycle Runner

Build062 executes the NRHIS operational data pipeline in a fixed, auditable order for the 7:00 AM and 6:00 PM reporting cycles.

## Sequence

1. Current USGS observations
2. Incremental USGS history update
3. NWPS forecast and threshold harvest
4. TWDB reservoir harvest
5. Reservoir evaporation and water budget
6. Estimated reservoir response
7. Reservoir operations summary
8. SALT03 coastal water-quality harvest
9. Integrated operations snapshot
10. Publication bundle and QA gate

A required-step failure stops downstream processing. Each step receives its own log, while the complete cycle writes a timestamped JSON receipt and a latest-cycle pointer. Publication authorization remains false unless the cycle completes and both QA passes are recorded.
