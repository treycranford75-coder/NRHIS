## NRHIS Sprint 2 - Build092

### USGS deep-history evidence and scale hardening

- adds USGS 08211503 and 0821150305 to the historical Nueces network;
- loads the historical identity index once per run instead of rescanning the growing JSONL on every chunk;
- preserves exact upstream USGS response bytes;
- makes each recorded raw SHA-256 verifiable against the archived file;
- preserves differing rerun responses instead of overwriting earlier evidence;
- expands PlanOnly output to list every configured station and parameter code;
- adds deterministic tests for deduplication scale behavior, raw evidence integrity, and Rincon coverage.

No production historical USGS requests are made by this build.
