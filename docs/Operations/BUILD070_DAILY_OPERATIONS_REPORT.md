# Build070 — Daily Operations Report Publisher

Build070 pivots NRHIS from infrastructure hardening to the operator-facing deliverable. It assembles verified NRHIS inputs into JSON, Markdown, and print-ready HTML while preserving the mandatory two-pass QA publication gate.

The report includes the four primary river stations, separate Choke Canyon and Lake Corpus Christi sections, evaporation and 24-hour water budgets, estimated reservoir response, SALT03 coastal water quality, scheduler health, alert severity, sources, limitations, and a durable JSONL history.

HTML is designed for browser printing to PDF after publication is authorized. Build070 does not silently fabricate missing values; unavailable inputs are labeled and required-source gaps hold publication.
