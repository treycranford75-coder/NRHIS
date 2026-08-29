from __future__ import annotations

import json
from pathlib import Path

repo = Path.cwd()
module_path = repo / "src" / "nrhis_harvest" / "usgs_historical_backfill.py"
config_path = repo / "config" / "nrhis" / "usgs_nueces_basin.json"
bootstrap_path = repo / "scripts" / "Bootstrap-USGS-History.ps1"

text = module_path.read_text(encoding="utf-8")

# 1. Exact-byte raw evidence writer. The receipt hash must hash the file actually preserved.
anchor = '''def load_json(path: Path) -> dict[str, Any]:\n'''
if "def write_raw_evidence(" not in text:
    if anchor not in text:
        raise SystemExit("Unable to locate raw-evidence insertion anchor.")
    addition = '''def write_raw_evidence(path: Path, raw: bytes) -> Path:\n    \"\"\"Preserve exact upstream bytes without overwriting differing evidence.\"\"\"\n    path.parent.mkdir(parents=True, exist_ok=True)\n    digest = hashlib.sha256(raw).hexdigest()\n    candidate = path\n    if candidate.exists():\n        if hashlib.sha256(candidate.read_bytes()).hexdigest() == digest:\n            return candidate\n        candidate = path.with_name(f\"{path.stem}-{digest[:12]}{path.suffix}\")\n        if candidate.exists():\n            if hashlib.sha256(candidate.read_bytes()).hexdigest() == digest:\n                return candidate\n            raise BackfillError(f\"Raw evidence hash collision at {candidate}\")\n    fd, temp_name = tempfile.mkstemp(prefix=candidate.name, suffix=\".tmp\", dir=candidate.parent)\n    try:\n        with os.fdopen(fd, \"wb\") as handle:\n            handle.write(raw)\n        os.replace(temp_name, candidate)\n    finally:\n        if os.path.exists(temp_name):\n            os.unlink(temp_name)\n    return candidate\n\n\n'''
    text = text.replace(anchor, addition + anchor, 1)

# 2. Duplicate index can be supplied once and updated in memory during the run.
old_append = '''def append_deduplicated(path: Path, records: Iterable[HistoricalObservation]) -> int:\n    known = existing_identities(path)\n    new_records = [record for record in records if record.identity not in known]\n    if new_records:\n        path.parent.mkdir(parents=True, exist_ok=True)\n        with path.open("a", encoding="utf-8", newline="") as handle:\n            for record in new_records:\n                handle.write(json.dumps(asdict(record), sort_keys=True, separators=(",", ":")) + "\\n")\n    return len(new_records)\n'''
new_append = '''def append_deduplicated(\n    path: Path,\n    records: Iterable[HistoricalObservation],\n    known: set[str] | None = None,\n) -> int:\n    if known is None:\n        known = existing_identities(path)\n    new_records: list[HistoricalObservation] = []\n    for record in records:\n        if record.identity in known:\n            continue\n        known.add(record.identity)\n        new_records.append(record)\n    if new_records:\n        path.parent.mkdir(parents=True, exist_ok=True)\n        with path.open("a", encoding="utf-8", newline="") as handle:\n            for record in new_records:\n                handle.write(json.dumps(asdict(record), sort_keys=True, separators=(",", ":")) + "\\n")\n    return len(new_records)\n'''
if old_append in text:
    text = text.replace(old_append, new_append, 1)
elif "known: set[str] | None = None" not in text:
    raise SystemExit("Unable to locate append_deduplicated implementation.")

# 3. Load identities once before the chunk loop and reuse the set.
paths_anchor = '''    history_path = output_root / "normalized" / "usgs_historical_observations.jsonl"\n    csv_path = output_root / "normalized" / "usgs_historical_observations.csv"\n'''
paths_replacement = paths_anchor + '''    known_identities = existing_identities(history_path)\n    existing_records_at_start = len(known_identities)\n'''
if "existing_records_at_start = len(known_identities)" not in text:
    if paths_anchor not in text:
        raise SystemExit("Unable to locate historical output path anchor.")
    text = text.replace(paths_anchor, paths_replacement, 1)

text = text.replace(
    "            new_records = append_deduplicated(history_path, records)\n",
    "            new_records = append_deduplicated(history_path, records, known_identities)\n",
    1,
)
if "append_deduplicated(history_path, records, known_identities)" not in text:
    raise SystemExit("Unable to install in-memory identity reuse.")

# 4. Preserve original response bytes; do not reserialize JSON as the raw artifact.
old_raw = '''            raw_path = output_root / "raw" / "usgs_iv_backfill" / f"usgs-iv-{chunk_start}-{chunk_end}.json"\n            atomic_write_text(raw_path, json.dumps(payload, indent=2, sort_keys=True) + "\\n")\n            new_records = append_deduplicated(history_path, records, known_identities)\n'''
new_raw = '''            raw_path = output_root / "raw" / "usgs_iv_backfill" / f"usgs-iv-{chunk_start}-{chunk_end}.json"\n            evidence_path = write_raw_evidence(raw_path, raw)\n            new_records = append_deduplicated(history_path, records, known_identities)\n'''
if old_raw in text:
    text = text.replace(old_raw, new_raw, 1)
elif "evidence_path = write_raw_evidence(raw_path, raw)" not in text:
    raise SystemExit("Unable to locate raw response preservation block.")
text = text.replace('                    "raw_file": str(raw_path),\n', '                    "raw_file": str(evidence_path),\n', 1)

# Add run-scale metadata to the receipt.
receipt_anchor = '''        "new_records": new_records_total,\n        "total_history_records": total_history_records,\n'''
receipt_new = '''        "new_records": new_records_total,\n        "existing_records_at_start": existing_records_at_start,\n        "identity_index_final_size": len(known_identities),\n        "total_history_records": total_history_records,\n'''
if "identity_index_final_size" not in text:
    if receipt_anchor not in text:
        raise SystemExit("Unable to locate receipt metadata anchor.")
    text = text.replace(receipt_anchor, receipt_new, 1)

module_path.write_text(text, encoding="utf-8", newline="\n")
print(f"Patched: {module_path}")

# 5. Extend the configured historical network with the two Rincon Bayou records.
config = json.loads(config_path.read_text(encoding="utf-8"))
stations = config.setdefault("stations", [])
existing = {str(station.get("site_no")) for station in stations}
additions = [
    {
        "site_no": "08211503",
        "name": "Rincon Bayou Channel near Calallen, TX",
        "segment": "Nueces Delta",
    },
    {
        "site_no": "0821150305",
        "name": "Rincon Bayou Channel near Odem, TX",
        "segment": "Nueces Delta",
    },
]
for station in additions:
    if station["site_no"] not in existing:
        stations.append(station)
config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8", newline="\n")
print(f"Patched: {config_path}")

# 6. Make PlanOnly show the actual station and parameter registry before a long run.
bootstrap = bootstrap_path.read_text(encoding="utf-8")
plan_anchor = '''Write-Host "  Output:     $OutputRoot"\nWrite-Host ""\n'''
plan_addition = '''Write-Host "  Output:     $OutputRoot"\nWrite-Host ""\nWrite-Host "Configured stations:" -ForegroundColor Cyan\nforeach ($station in @($config.stations)) {\n    Write-Host ("  {0}  {1}  [{2}]" -f $station.site_no, $station.name, $station.segment)\n}\nWrite-Host "Configured parameter codes: $(@($config.parameter_codes) -join ', ')"\nWrite-Host "USGS returns only series that actually exist for a station and period." -ForegroundColor DarkGray\nWrite-Host ""\n'''
if "Configured stations:" not in bootstrap:
    if plan_anchor not in bootstrap:
        raise SystemExit("Unable to locate Bootstrap-USGS-History plan anchor.")
    bootstrap = bootstrap.replace(plan_anchor, plan_addition, 1)
bootstrap_path.write_text(bootstrap, encoding="utf-8", newline="\n")
print(f"Patched: {bootstrap_path}")
