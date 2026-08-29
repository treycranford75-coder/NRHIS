from __future__ import annotations

from pathlib import Path


def main() -> int:
    repo = Path.cwd()
    target = repo / "src" / "nrhis_harvest" / "usgs_historical_backfill.py"
    if not target.is_file():
        raise SystemExit(f"Missing target module: {target}")

    text = target.read_text(encoding="utf-8")

    helper_anchor = '''def existing_identities(path: Path) -> set[str]:\n'''
    helper = '''def resolve_resume_start(\n    checkpoint: dict[str, Any], requested_start: date\n) -> tuple[date, bool, str | None]:\n    """Return a safe resume start without allowing a newer checkpoint to hide older history."""\n    completed_raw = checkpoint.get("completed_through")\n    checkpoint_start_raw = checkpoint.get("requested_start")\n    if not completed_raw or not checkpoint_start_raw:\n        return requested_start, False, "checkpoint_missing_scope"\n\n    checkpoint_start = parse_iso_date(str(checkpoint_start_raw))\n    if checkpoint_start != requested_start:\n        return requested_start, False, "checkpoint_requested_start_mismatch"\n\n    candidate = parse_iso_date(str(completed_raw)) + timedelta(days=1)\n    return max(requested_start, candidate), True, None\n\n\n'''

    if "def resolve_resume_start(" not in text:
        if helper_anchor not in text:
            raise SystemExit("Unable to locate existing_identities anchor in historical backfill module.")
        text = text.replace(helper_anchor, helper + helper_anchor, 1)

    old_block = '''    checkpoint_path = output_root / "backfill" / "checkpoint.json"\n    effective_start = requested_start\n    if resume and checkpoint_path.exists():\n        checkpoint = load_json(checkpoint_path)\n        if checkpoint.get("completed_through"):\n            candidate = parse_iso_date(str(checkpoint["completed_through"])) + timedelta(days=1)\n            if candidate > effective_start:\n                effective_start = candidate\n'''
    new_block = '''    checkpoint_path = output_root / "backfill" / "checkpoint.json"\n    effective_start = requested_start\n    checkpoint_used = False\n    checkpoint_ignored_reason: str | None = None\n    if resume and checkpoint_path.exists():\n        checkpoint = load_json(checkpoint_path)\n        effective_start, checkpoint_used, checkpoint_ignored_reason = resolve_resume_start(\n            checkpoint, requested_start\n        )\n'''

    if old_block in text:
        text = text.replace(old_block, new_block, 1)
    elif "checkpoint_used = False" not in text:
        raise SystemExit("Unable to locate the Build052 checkpoint block to replace.")

    receipt_anchor = '''        "effective_start": effective_start.isoformat(),\n        "chunk_days": chunk_days,\n'''
    receipt_replacement = '''        "effective_start": effective_start.isoformat(),\n        "checkpoint_used": checkpoint_used,\n        "checkpoint_ignored_reason": checkpoint_ignored_reason,\n        "chunk_days": chunk_days,\n'''
    if receipt_anchor in text:
        text = text.replace(receipt_anchor, receipt_replacement, 1)
    elif '"checkpoint_used": checkpoint_used' not in text:
        raise SystemExit("Unable to locate receipt checkpoint fields.")

    target.write_text(text, encoding="utf-8", newline="\n")
    print(f"Build090 patched {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
