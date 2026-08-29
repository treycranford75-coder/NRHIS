# Build099 - Rincon Evidence Reconciliation

Build099 reconciles two intentionally different interval definitions used by NRHIS:

- Build097: contiguous runs of sampled discharge values below zero.
- Build098: contiguous negative portions of piecewise-linearly interpolated observation pairs.

A single exact-zero sample between negative observations splits Build097 into two sampled-value runs, but Build098's negative pieces touch at that solved zero and remain one integrated interval. Build099 maps the two interval families, enumerates exact-zero bridges, reports any observation-only runs that cannot be integrated because of data boundaries or gaps, and verifies the count identity.

The build also creates a critical evidence timeline around the longest material discharge gap and the terminal discharge discontinuation, including the exact integrated reverse-flow interval that terminates at the pre-gap observation, stage coverage during the gap, the first reverse interval after discharge resumes, and stage monitoring after discharge ends.

No network requests are made. All outputs are SHA-256 bound to the finalized NRHIS archive and sparse query index.
