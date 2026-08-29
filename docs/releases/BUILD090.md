# NRHIS Sprint 2 - Build090

Build090 restores direct hydrologic development after the Build086-Build089 release-lifecycle stabilization sequence.

It fixes historical USGS checkpoint scope so recent-range checkpoints cannot silently hide older requested history, adds a dedicated deep-history bootstrap command, and preserves the existing raw-response archive, normalized observation store, duplicate protection, chunk receipts, and restart behavior.
