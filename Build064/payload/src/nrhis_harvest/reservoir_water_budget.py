"""Reservoir evaporation and 24-hour water-budget products for NRHIS Build056."""
from __future__ import annotations

import csv
import json
import os
import tempfile
from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

ACRE_FOOT_GALLONS = 325851.0


@dataclass(frozen=True)
class ReservoirBudget:
    reservoir_id: str
    reservoir_name: str
    report_date: str
    surface_area_acres: float | None
    evaporation_inches_per_day: float | None
    evaporation_source: str
    evaporation_method: str
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


def _num(value: Any) -> float | None:
    try:
        return None if value in (None, "") else float(value)
    except (TypeError, ValueError):
        return None


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            handle.write(text)
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def _load_optional(path: Path) -> Any:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def evaporation_acft(surface_area_acres: float | None, inches_per_day: float | None) -> float | None:
    if surface_area_acres is None or inches_per_day is None:
        return None
    return round(surface_area_acres * inches_per_day / 12.0, 3)


def _daily_evap(evap_data: Any, reservoir_id: str, report_date: str) -> tuple[float | None, str, str]:
    if isinstance(evap_data, list):
        for row in evap_data:
            if row.get("reservoir_id") == reservoir_id and row.get("date") == report_date:
                value = _num(row.get("evaporation_inches"))
                if value is not None:
                    return value, str(row.get("source") or "daily evaporation dataset"), "daily observed/estimated evaporation"
    return None, "", ""


def build_budget(
    reservoirs: list[dict[str, Any]],
    config: dict[str, Any],
    *,
    report_date: date,
    evaporation_data: Any = None,
    flux_data: Any = None,
    history_rows: list[dict[str, Any]] | None = None,
) -> list[ReservoirBudget]:
    result: list[ReservoirBudget] = []
    history_rows = history_rows or []
    climate = config["monthly_climatology_inches_per_day"]
    flux_lookup = {r.get("reservoir_id"): r for r in (flux_data or []) if isinstance(r, dict)}
    for reservoir in reservoirs:
        rid = str(reservoir["reservoir_id"])
        evap_in, source, method = _daily_evap(evaporation_data, rid, report_date.isoformat())
        if evap_in is None:
            evap_in = _num(climate[str(report_date.month)])
            source = "configured monthly climatology fallback"
            method = f"monthly climatology for month {report_date.month}; estimate"
        area = _num(reservoir.get("surface_area_acres"))
        evap_af = evaporation_acft(area, evap_in)
        matching = [r for r in history_rows if r.get("reservoir_id") == rid and r.get("report_date", "") <= report_date.isoformat()]
        matching.sort(key=lambda r: r.get("report_date", ""))
        recent = matching[-6:]
        recent_total = sum(_num(r.get("evaporation_acft_per_day")) or 0 for r in recent) + (evap_af or 0)
        month_total = sum((_num(r.get("evaporation_acft_per_day")) or 0) for r in matching if str(r.get("report_date", "")).startswith(report_date.strftime("%Y-%m"))) + (evap_af or 0)
        flux = flux_lookup.get(rid, {})
        inflow = _num(flux.get("inflow_acft"))
        diversions = _num(flux.get("municipal_diversions_acft"))
        releases = _num(flux.get("environmental_releases_acft"))
        other = _num(flux.get("other_outflow_acft")) or 0.0
        observed = _num(reservoir.get("storage_change_acft"))
        complete = all(v is not None for v in (inflow, diversions, releases, evap_af))
        calculated = None
        residual = None
        if complete:
            calculated = round(inflow - diversions - releases - other - evap_af, 3)
            if observed is not None:
                residual = round(observed - calculated, 3)
        result.append(ReservoirBudget(
            reservoir_id=rid,
            reservoir_name=str(reservoir.get("reservoir_name") or config["reservoirs"].get(rid, {}).get("display_name") or rid),
            report_date=report_date.isoformat(),
            surface_area_acres=area,
            evaporation_inches_per_day=evap_in,
            evaporation_source=source,
            evaporation_method=method,
            evaporation_acft_per_day=evap_af,
            evaporation_mgd=round(evap_af * ACRE_FOOT_GALLONS / 1_000_000, 3) if evap_af is not None else None,
            evaporation_7day_acft=round(recent_total, 3),
            evaporation_month_to_date_acft=round(month_total, 3),
            inflow_acft=inflow,
            municipal_diversions_acft=diversions,
            environmental_releases_acft=releases,
            other_outflow_acft=other,
            observed_storage_change_acft=observed,
            calculated_net_change_acft=calculated,
            budget_residual_acft=residual,
            budget_complete=complete,
        ))
    return result


def run(config_path: Path, data_root: Path, *, report_date: date | None = None) -> dict[str, Any]:
    report_date = report_date or datetime.now(timezone.utc).date()
    config = json.loads(config_path.read_text(encoding="utf-8"))
    reservoirs_path = data_root / "reservoirs" / "reservoir_current_conditions.json"
    reservoirs = json.loads(reservoirs_path.read_text(encoding="utf-8"))
    evap_data = _load_optional(Path(config["daily_evaporation_path"]))
    flux_data = _load_optional(Path(config["daily_fluxes_path"]))
    history_path = Path(config["history_path"])
    history_rows = []
    if history_path.exists():
        history_rows = [json.loads(line) for line in history_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    budgets = build_budget(reservoirs, config, report_date=report_date, evaporation_data=evap_data, flux_data=flux_data, history_rows=history_rows)
    rows = [asdict(x) for x in budgets]
    out_dir = data_root / "reservoirs"
    json_path = out_dir / "reservoir_water_budget_current.json"
    csv_path = out_dir / "reservoir_water_budget_current.csv"
    _atomic_write(json_path, json.dumps(rows, indent=2, sort_keys=True) + "\n")
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader(); writer.writerows(rows)
    existing_ids = {(r.get("reservoir_id"), r.get("report_date")) for r in history_rows}
    new_rows = [r for r in rows if (r["reservoir_id"], r["report_date"]) not in existing_ids]
    if new_rows:
        history_path.parent.mkdir(parents=True, exist_ok=True)
        with history_path.open("a", encoding="utf-8") as handle:
            for row in new_rows:
                handle.write(json.dumps(row, separators=(",", ":"), sort_keys=True) + "\n")
    summary = {
        "schema_version": 1,
        "build": "056",
        "report_date": report_date.isoformat(),
        "reservoir_count": len(rows),
        "all_budgets_complete": all(r["budget_complete"] for r in rows),
        "combined_evaporation_acft_per_day": round(sum(r["evaporation_acft_per_day"] or 0 for r in rows), 3),
        "combined_evaporation_mgd": round(sum(r["evaporation_mgd"] or 0 for r in rows), 3),
        "reservoirs": rows,
    }
    summary_path = out_dir / "reservoir_water_budget_summary.json"
    _atomic_write(summary_path, json.dumps(summary, indent=2, sort_keys=True) + "\n")
    receipt = {"schema_version": 1, "build": "056", "completed_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"), "new_history_records": len(new_rows), "files": {"current_json": str(json_path), "current_csv": str(csv_path), "summary": str(summary_path), "history": str(history_path)}}
    receipt_path = data_root / "receipts" / "reservoir_water_budget_receipt.json"
    _atomic_write(receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    receipt["receipt_path"] = str(receipt_path)
    return receipt
