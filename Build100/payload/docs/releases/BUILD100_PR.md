## Build100 — Formal Rincon Evidence Report

- Adds a report generator over reconciled Build099 evidence.
- Emits Markdown, CSV findings, and a SHA-256 receipt.
- Preserves the exact pre-gap integrated reverse-flow evidence.
- Marks discharge-outage and post-terminal periods as unobservable rather than estimated.
- Relabels the Build099 terminal-discharge legacy field in report output without mutating upstream evidence.
- Local-only; zero USGS requests; no archive changes.
