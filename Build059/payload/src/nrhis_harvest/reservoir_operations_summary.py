"""Integrated reservoir operations summary for NRHIS Build058."""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ReservoirOperationsRow:
    reservoir_id: str
    reservoir_name: str
    current_storage_acft: float | None
    conservation_capacity_acft: float | None
    current_percent_full: float | None
    surface_area_acres: float | None
    evaporation_acft_per_day: float | None
    evaporation_mgd: float | None
    evaporation_7day_acft: float | None
    evaporation_month_to_date_acft: float | None
    inflow_acft: float | None
    municipal_diversions_acft: float | None
    environmental_releases_acft: float | None
    other_outflow_acft: float | None
    observed_storage_change_acft: float | None
    calculated_net_change_acft: float | None
    budget_residual_acft: float | None
    budget_complete: bool
    estimated_event_gain_low_acft: float | None
    estimated_event_gain_central_acft: float | None
    estimated_event_gain_high_acft: float | None
    projected_storage_central_acft: float | None
    projected_percent_full_central: float | None
    response_confidence: str
    response_basis: str
    response_caveat: str
    operations_status: str
    status_reasons: str


def _num(value: Any) -> float | None:
    try:
        return None if value in (None, "", "null") else float(value)
    except (TypeError, ValueError):
        return None


def _index(rows: list[dict[str, Any]], key: str = "reservoir_id") -> dict[str, dict[str, Any]]:
    return {str(row.get(key, "")): row for row in rows if isinstance(row, dict) and row.get(key)}


def _load_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    value = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(value, list):
        return [row for row in value if isinstance(row, dict)]
    if isinstance(value, dict) and isinstance(value.get("reservoirs"), list):
        return [row for row in value["reservoirs"] if isinstance(row, dict)]
    return []


def build_summary(
    current_rows: list[dict[str, Any]],
    budget_rows: list[dict[str, Any]],
    response_rows: list[dict[str, Any]],
    config: dict[str, Any],
) -> list[ReservoirOperationsRow]:
    current = _index(current_rows)
    budgets = _index(budget_rows)
    responses = _index(response_rows)
    result: list[ReservoirOperationsRow] = []

    for rid in config.get("reservoir_order", []):
        c = current.get(rid, {})
        b = budgets.get(rid, {})
        r = responses.get(rid, {})
        reasons: list[str] = []

        storage = _num(c.get("conservation_storage_acft"))
        capacity = _num(c.get("conservation_capacity_acft"))
        percent = _num(c.get("percent_full"))
        if storage is None or capacity is None or percent is None:
            reasons.append("current reservoir storage data incomplete")
        if c.get("stale") is True:
            reasons.append("current reservoir observation is stale")

        budget_complete = bool(b.get("budget_complete", False))
        if not budget_complete:
            reasons.append("24-hour water budget incomplete")

        confidence = str(r.get("confidence") or "low")
        if confidence.lower() == "low":
            reasons.append("estimated reservoir response confidence is low")

        if not c:
            reasons.append("current reservoir record missing")
        if not b:
            reasons.append("water-budget record missing")
        if not r:
            reasons.append("estimated-response record missing")

        status = "ready" if not reasons else "conditional"
        if not c or storage is None or capacity is None:
            status = "not_ready"

        result.append(
            ReservoirOperationsRow(
                reservoir_id=rid,
                reservoir_name=str(
                    c.get("reservoir_name")
                    or r.get("reservoir_name")
                    or config.get("display_names", {}).get(rid, rid)
                ),
                current_storage_acft=storage,
                conservation_capacity_acft=capacity,
                current_percent_full=percent,
                surface_area_acres=_num(c.get("surface_area_acres")),
                evaporation_acft_per_day=_num(b.get("evaporation_acft_per_day")),
                evaporation_mgd=_num(b.get("evaporation_mgd")),
                evaporation_7day_acft=_num(b.get("evaporation_7day_acft")),
                evaporation_month_to_date_acft=_num(b.get("evaporation_month_to_date_acft")),
                inflow_acft=_num(b.get("inflow_acft")),
                municipal_diversions_acft=_num(b.get("municipal_diversions_acft")),
                environmental_releases_acft=_num(b.get("environmental_releases_acft")),
                other_outflow_acft=_num(b.get("other_outflow_acft")),
                observed_storage_change_acft=_num(b.get("observed_storage_change_acft")),
                calculated_net_change_acft=_num(b.get("calculated_net_change_acft")),
                budget_residual_acft=_num(b.get("budget_residual_acft")),
                budget_complete=budget_complete,
                estimated_event_gain_low_acft=_num(r.get("estimated_event_gain_low_acft")),
                estimated_event_gain_central_acft=_num(r.get("estimated_event_gain_central_acft")),
                estimated_event_gain_high_acft=_num(r.get("estimated_event_gain_high_acft")),
                projected_storage_central_acft=_num(r.get("projected_storage_central_acft")),
                projected_percent_full_central=_num(r.get("projected_percent_full_central")),
                response_confidence=confidence,
                response_basis=str(r.get("basis") or ""),
                response_caveat=str(r.get("caveat") or ""),
                operations_status=status,
                status_reasons="; ".join(reasons),
            )
        )
    return result


def run(config_path: Path, data_root: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    reservoir_dir = data_root / "reservoirs"
    current_rows = _load_rows(reservoir_dir / "reservoir_current_conditions.json")
    budget_rows = _load_rows(reservoir_dir / "reservoir_water_budget_current.json")
    response_rows = _load_rows(reservoir_dir / "reservoir_response_estimate.json")

    rows = [asdict(row) for row in build_summary(current_rows, budget_rows, response_rows, config)]
    reservoir_dir.mkdir(parents=True, exist_ok=True)
    json_path = reservoir_dir / "reservoir_operations_summary.json"
    csv_path = reservoir_dir / "reservoir_operations_summary.csv"
    readiness_path = reservoir_dir / "reservoir_operations_readiness.json"

    json_path.write_text(json.dumps(rows, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()) if rows else ["reservoir_id"])
        writer.writeheader()
        writer.writerows(rows)

    overall = "ready"
    if any(row["operations_status"] == "not_ready" for row in rows):
        overall = "not_ready"
    elif any(row["operations_status"] == "conditional" for row in rows):
        overall = "conditional"

    readiness = {
        "schema_version": 1,
        "build": "058",
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "overall_status": overall,
        "reservoir_count": len(rows),
        "ready_count": sum(row["operations_status"] == "ready" for row in rows),
        "conditional_count": sum(row["operations_status"] == "conditional" for row in rows),
        "not_ready_count": sum(row["operations_status"] == "not_ready" for row in rows),
        "reservoirs": [
            {
                "reservoir_id": row["reservoir_id"],
                "status": row["operations_status"],
                "reasons": row["status_reasons"],
            }
            for row in rows
        ],
    }
    readiness_path.write_text(json.dumps(readiness, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    receipt = {
        "schema_version": 1,
        "build": "058",
        "completed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "reservoir_count": len(rows),
        "overall_status": overall,
        "files": {
            "json": str(json_path),
            "csv": str(csv_path),
            "readiness": str(readiness_path),
        },
    }
    receipt_path = data_root / "receipts" / "reservoir_operations_summary_receipt.json"
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    receipt["receipt_path"] = str(receipt_path)
    return receipt
