# NRHIS System Architecture

NRHIS uses a controlled pipeline:

1. Harvest authoritative observations.
2. Preserve immutable raw records.
3. Standardize observations.
4. Apply QA flags without altering source values.
5. Associate records with events and reaches.
6. Run versioned models.
7. generate GIS and publication outputs from frozen snapshots.
8. Archive the evidence chain.
