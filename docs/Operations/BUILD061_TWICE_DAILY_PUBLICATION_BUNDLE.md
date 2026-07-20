# Build061 — Twice-Daily Publication Bundle

Build061 converts the integrated operational snapshot into a publication-ready data package for the 7:00 AM and 6:00 PM NRHIS reports.

It does not generate a map or public graphic. It creates the verified data bundle and enforces the release gate that must be satisfied before graphic generation.

## Mandatory gates

1. Source-data verification pass.
2. Independent final-value and narrative verification pass.
3. Post-generation visual QA remains mandatory after a graphic is created.

A report is not authorized for publication unless the integrated source status is `ready`, every required section is present, and both verification passes are recorded.
