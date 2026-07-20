"""Build061 publication bundle and two-pass QA release gate."""
from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class PublicationGate:
    status: str
    publish_allowed: bool
    reasons: list[str]
    qa_passes_required: int
    qa_passes_completed: int


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(text, encoding="utf-8", newline="")
    temp.replace(path)


def _section_present(snapshot: dict[str, Any], section: str) -> bool:
    value = snapshot.get(section)
    return value not in (None, {}, [])


def evaluate_gate(
    snapshot: dict[str, Any],
    *,
    required_sections: list[str],
    qa_passes_completed: int,
    qa_passes_required: int = 2,
) -> PublicationGate:
    reasons: list[str] = []
    readiness = str(snapshot.get("overall_status") or snapshot.get("status") or "not_ready")
    for section in required_sections:
        if not _section_present(snapshot, section):
            reasons.append(f"missing required section: {section}")
    if readiness == "not_ready":
        reasons.append("integrated source snapshot is not ready")
    if qa_passes_completed < qa_passes_required:
        reasons.append(
            f"QA incomplete: {qa_passes_completed} of {qa_passes_required} verification passes completed"
        )
    publish_allowed = not reasons and readiness == "ready"
    if publish_allowed:
        status = "ready"
    elif readiness == "conditional" and not any(r.startswith("missing") for r in reasons):
        status = "conditional"
    else:
        status = "not_ready"
    return PublicationGate(
        status=status,
        publish_allowed=publish_allowed,
        reasons=reasons,
        qa_passes_required=qa_passes_required,
        qa_passes_completed=qa_passes_completed,
    )


def flatten_public_rows(snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    river = snapshot.get("river") or {}
    stations = river.get("stations") if isinstance(river, dict) else None
    if isinstance(stations, list):
        for station in stations:
            if isinstance(station, dict):
                rows.append({"section": "river", **station})
    reservoirs = snapshot.get("reservoirs") or {}
    items = reservoirs.get("reservoirs") if isinstance(reservoirs, dict) else None
    if isinstance(items, list):
        for reservoir in items:
            if isinstance(reservoir, dict):
                rows.append({"section": "reservoir", **reservoir})
    coastal = snapshot.get("coastal") or {}
    if isinstance(coastal, dict):
        rows.append({"section": "coastal", **coastal})
    return rows


def build_bundle(
    snapshot: dict[str, Any],
    *,
    qa_passes_completed: int,
    required_sections: list[str],
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    generated_at = generated_at or datetime.now(timezone.utc)
    gate = evaluate_gate(
        snapshot,
        required_sections=required_sections,
        qa_passes_completed=qa_passes_completed,
    )
    return {
        "schema_version": 1,
        "build": "061",
        "generated_at": generated_at.isoformat().replace("+00:00", "Z"),
        "publication_status": gate.status,
        "publish_allowed": gate.publish_allowed,
        "release_gate": asdict(gate),
        "public_data": snapshot,
        "qa": {
            "pass_1": "source values, timestamps, units, calculations, labels, and status categories verified",
            "pass_2": "final values and narrative independently rechecked immediately before publication",
            "post_generation_visual_qa_required": True,
            "graphic_generation_authorized": gate.publish_allowed,
        },
    }


def run(
    config_path: Path,
    data_root: Path,
    *,
    qa_passes_completed: int = 0,
) -> dict[str, Any]:
    config = _read_json(config_path)
    source = Path(config["source_snapshot"])
    if not source.is_absolute():
        source = data_root.parent.parent / source
    snapshot = _read_json(source)
    bundle = build_bundle(
        snapshot,
        qa_passes_completed=qa_passes_completed,
        required_sections=list(config["required_sections"]),
    )
    out_dir = data_root / "publication"
    bundle_path = out_dir / "twice_daily_publication_bundle.json"
    gate_path = out_dir / "publication_release_gate.json"
    qa_path = out_dir / "publication_qa_checklist.json"
    rows_path = out_dir / "publication_public_rows.csv"
    _atomic_write(bundle_path, json.dumps(bundle, indent=2, sort_keys=True) + "\n")
    _atomic_write(gate_path, json.dumps(bundle["release_gate"], indent=2, sort_keys=True) + "\n")
    _atomic_write(qa_path, json.dumps(bundle["qa"], indent=2, sort_keys=True) + "\n")
    rows = flatten_public_rows(snapshot)
    rows_path.parent.mkdir(parents=True, exist_ok=True)
    if rows:
        fields = sorted({key for row in rows for key in row})
        with rows_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
    else:
        rows_path.write_text("section\n", encoding="utf-8")
    receipt = {
        "schema_version": 1,
        "build": "061",
        "completed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "publication_status": bundle["publication_status"],
        "publish_allowed": bundle["publish_allowed"],
        "files": {
            "bundle": str(bundle_path),
            "gate": str(gate_path),
            "qa": str(qa_path),
            "public_rows": str(rows_path),
        },
    }
    receipt_path = data_root / "receipts" / "publication_bundle_receipt.json"
    _atomic_write(receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    receipt["receipt_path"] = str(receipt_path)
    return receipt
