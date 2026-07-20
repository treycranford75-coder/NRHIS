from __future__ import annotations

import argparse
import html
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any] | list[Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def _number(value: Any, digits: int = 1) -> str:
    if value is None or value == "":
        return "Not available"
    try:
        return f"{float(value):,.{digits}f}"
    except (TypeError, ValueError):
        return str(value)


def _first(mapping: Any, *keys: str) -> Any:
    if not isinstance(mapping, dict):
        return None
    for key in keys:
        if mapping.get(key) not in (None, ""):
            return mapping[key]
    return None


def _records(value: Any) -> list[dict[str, Any]]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if not isinstance(value, dict):
        return []
    for key in ("stations", "observations", "records", "rows", "reservoirs", "items"):
        candidate = value.get(key)
        if isinstance(candidate, list):
            return [item for item in candidate if isinstance(item, dict)]
    return []


def _station_rows(usgs: Any, configured: list[dict[str, Any]]) -> list[dict[str, Any]]:
    available = _records(usgs)
    rows: list[dict[str, Any]] = []
    for station in configured:
        site = station["site_no"]
        match = next(
            (
                row
                for row in available
                if str(_first(row, "site_no", "site", "station_id", "usgs_site")) == site
            ),
            {},
        )
        rows.append(
            {
                "site_no": site,
                "label": station["label"],
                "discharge_cfs": _first(match, "discharge_cfs", "flow_cfs", "00060", "discharge"),
                "gage_height_ft": _first(match, "gage_height_ft", "stage_ft", "00065", "stage"),
                "specific_conductance_us_cm": _first(
                    match, "specific_conductance_us_cm", "conductance", "00095"
                ),
                "observed_at": _first(match, "observed_at", "datetime", "timestamp", "date_time"),
                "status": "available" if match else "missing",
            }
        )
    return rows


def _reservoir_rows(
    summary: Any,
    budget: Any,
    response: Any,
    configured: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    summary_rows = _records(summary)
    budget_rows = _records(budget)
    response_rows = _records(response)

    def find(rows: list[dict[str, Any]], rid: str, label: str) -> dict[str, Any]:
        names = {rid.lower(), label.lower()}
        return next(
            (
                row
                for row in rows
                if str(_first(row, "reservoir_id", "id", "name", "reservoir")).lower()
                in names
            ),
            {},
        )

    output: list[dict[str, Any]] = []
    for reservoir in configured:
        rid, label = reservoir["id"], reservoir["label"]
        current = find(summary_rows, rid, label)
        wb = find(budget_rows, rid, label)
        rr = find(response_rows, rid, label)
        output.append(
            {
                "id": rid,
                "label": label,
                "storage_acft": _first(current, "storage_acft", "storage", "conservation_storage_acft"),
                "percent_full": _first(current, "percent_full", "pct_full", "conservation_percent"),
                "surface_area_acres": _first(current, "surface_area_acres", "surface_area"),
                "evaporation_acft_day": _first(wb, "evaporation_acft_day", "evaporation_af_day"),
                "evaporation_mgd": _first(wb, "evaporation_mgd"),
                "evaporation_7d_acft": _first(wb, "evaporation_7d_acft", "seven_day_evaporation_acft"),
                "evaporation_mtd_acft": _first(wb, "evaporation_mtd_acft", "month_to_date_evaporation_acft"),
                "inflow_acft_day": _first(wb, "inflow_acft_day", "inflow_af_day"),
                "diversions_acft_day": _first(wb, "diversions_acft_day", "municipal_diversions_acft_day"),
                "releases_acft_day": _first(wb, "releases_acft_day", "environmental_releases_acft_day"),
                "net_storage_change_acft_day": _first(wb, "net_storage_change_acft_day", "net_change_acft_day"),
                "event_gain_low_acft": _first(rr, "event_gain_low_acft", "estimated_gain_low_acft"),
                "event_gain_high_acft": _first(rr, "event_gain_high_acft", "estimated_gain_high_acft"),
                "projected_storage_low_acft": _first(rr, "projected_storage_low_acft"),
                "projected_storage_high_acft": _first(rr, "projected_storage_high_acft"),
                "confidence": _first(rr, "confidence", "confidence_level"),
                "status": "available" if current else "missing",
            }
        )
    return output


def _markdown(report: dict[str, Any]) -> str:
    lines = [
        f"# {report['report_title']}",
        "",
        f"**Generated:** {report['generated_at']}  ",
        f"**Publication status:** {report['publication_status']}  ",
        f"**QA passes completed:** {report['qa_passes_completed']}  ",
        "",
    ]
    if report["release_hold_reasons"]:
        lines += ["## Release hold", ""] + [f"- {x}" for x in report["release_hold_reasons"]] + [""]

    lines += [
        "## River and station conditions",
        "",
        "| Station | Flow (cfs) | Stage (ft) | Conductance (µS/cm) | Observation time |",
        "|---|---:|---:|---:|---|",
    ]
    for row in report["stations"]:
        lines.append(
            f"| {row['label']} ({row['site_no']}) | {_number(row['discharge_cfs'])} | "
            f"{_number(row['gage_height_ft'], 2)} | {_number(row['specific_conductance_us_cm'])} | "
            f"{row['observed_at'] or 'Not available'} |"
        )

    lines += ["", "## Reservoir operations", ""]
    for row in report["reservoirs"]:
        lines += [
            f"### {row['label']}",
            "",
            f"- Current storage: {_number(row['storage_acft'], 0)} acre-feet ({_number(row['percent_full'])}% full)",
            f"- Surface area: {_number(row['surface_area_acres'], 0)} acres",
            f"- Evaporation: {_number(row['evaporation_acft_day'])} acre-feet/day; {_number(row['evaporation_mgd'])} MGD",
            f"- Evaporation totals: {_number(row['evaporation_7d_acft'])} acre-feet (7-day); {_number(row['evaporation_mtd_acft'])} acre-feet (month-to-date)",
            f"- 24-hour water budget: inflow {_number(row['inflow_acft_day'])}, diversions {_number(row['diversions_acft_day'])}, releases {_number(row['releases_acft_day'])}, net storage change {_number(row['net_storage_change_acft_day'])} acre-feet/day",
            f"- Estimated event gain: {_number(row['event_gain_low_acft'], 0)} to {_number(row['event_gain_high_acft'], 0)} acre-feet",
            f"- Projected post-event storage: {_number(row['projected_storage_low_acft'], 0)} to {_number(row['projected_storage_high_acft'], 0)} acre-feet",
            f"- Confidence: {row['confidence'] or 'Not available'}",
            "",
        ]

    coastal = report["coastal_water_quality"]
    lines += [
        "## Coastal water quality — SALT03",
        "",
        f"- Salinity: {_number(_first(coastal, 'salinity_psu', 'salinity'))} PSU",
        f"- Specific conductance: {_number(_first(coastal, 'specific_conductance_us_cm', 'conductance'))} µS/cm",
        f"- Observation time: {_first(coastal, 'observed_at', 'timestamp', 'datetime') or 'Not available'}",
        "",
        "## Operational health",
        "",
        f"- Scheduler health: {_first(report['scheduler_health'], 'status') or 'Not available'}",
        f"- Scheduler alert severity: {_first(report['scheduler_alert'], 'severity') or 'Not available'}",
        "",
        "## Sources and limitations",
        "",
        "Current USGS observations are intended to come from the USGS Instantaneous Values service. NWPS forecast products provide forecast context and flood thresholds. Reservoir values, evaporation, water-budget, response, and SALT03 entries are reported only when present in the verified NRHIS inputs.",
        "",
        "Estimated reservoir response is based on the latest available hydrographs, routing assumptions, reservoir conditions, and forecasts and will change as new data arrive.",
    ]
    return "\n".join(lines) + "\n"


def _html(report: dict[str, Any], markdown_text: str) -> str:
    station_rows = "".join(
        "<tr>"
        f"<td>{html.escape(row['label'])}<br><small>{row['site_no']}</small></td>"
        f"<td>{_number(row['discharge_cfs'])}</td>"
        f"<td>{_number(row['gage_height_ft'], 2)}</td>"
        f"<td>{_number(row['specific_conductance_us_cm'])}</td>"
        f"<td>{html.escape(str(row['observed_at'] or 'Not available'))}</td>"
        "</tr>"
        for row in report["stations"]
    )
    reservoir_cards = "".join(
        f"<section class='card'><h2>{html.escape(row['label'])}</h2>"
        f"<p><b>Storage:</b> {_number(row['storage_acft'],0)} acre-feet ({_number(row['percent_full'])}% full)</p>"
        f"<p><b>Evaporation:</b> {_number(row['evaporation_acft_day'])} acre-feet/day; {_number(row['evaporation_mgd'])} MGD</p>"
        f"<p><b>7-day / MTD evaporation:</b> {_number(row['evaporation_7d_acft'])} / {_number(row['evaporation_mtd_acft'])} acre-feet</p>"
        f"<p><b>24-hour budget:</b> inflow {_number(row['inflow_acft_day'])}; diversions {_number(row['diversions_acft_day'])}; releases {_number(row['releases_acft_day'])}; net {_number(row['net_storage_change_acft_day'])} acre-feet/day</p>"
        f"<p><b>Estimated event gain:</b> {_number(row['event_gain_low_acft'],0)}–{_number(row['event_gain_high_acft'],0)} acre-feet; confidence {html.escape(str(row['confidence'] or 'Not available'))}</p></section>"
        for row in report["reservoirs"]
    )
    hold = "" if not report["release_hold_reasons"] else (
        "<div class='hold'><b>Release held:</b><ul>" + "".join(
            f"<li>{html.escape(reason)}</li>" for reason in report["release_hold_reasons"]
        ) + "</ul></div>"
    )
    return f"""<!doctype html>
<html lang='en'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>
<title>{html.escape(report['report_title'])}</title>
<style>
body{{font-family:Arial,sans-serif;margin:0;background:#f4f6f8;color:#17202a}}main{{max-width:1100px;margin:auto;padding:28px}}header{{background:#123b5d;color:white;padding:24px;border-radius:10px}}.meta{{display:flex;gap:20px;flex-wrap:wrap}}.status{{font-weight:bold;text-transform:uppercase}}.hold{{background:#fff3cd;border:1px solid #e0b100;padding:14px;margin:18px 0}}table{{width:100%;border-collapse:collapse;background:white}}th,td{{padding:10px;border:1px solid #d5d8dc;text-align:left}}th{{background:#eaf2f8}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:16px}}.card{{background:white;padding:18px;border-radius:8px;box-shadow:0 1px 4px #0002}}footer{{margin-top:24px;font-size:.9em;color:#566573}}@media print{{body{{background:white}}main{{max-width:none;padding:0}}.card{{box-shadow:none;border:1px solid #ccc}}}}
</style></head><body><main>
<header><h1>{html.escape(report['report_title'])}</h1><div class='meta'><span>Generated: {html.escape(report['generated_at'])}</span><span class='status'>Status: {html.escape(report['publication_status'])}</span><span>QA passes: {report['qa_passes_completed']}</span></div></header>
{hold}<h2>River and station conditions</h2><table><thead><tr><th>Station</th><th>Flow (cfs)</th><th>Stage (ft)</th><th>Conductance (µS/cm)</th><th>Observed</th></tr></thead><tbody>{station_rows}</tbody></table>
<h2>Reservoir operations</h2><div class='grid'>{reservoir_cards}</div>
<h2>Coastal water quality — SALT03</h2><section class='card'><p><b>Salinity:</b> {_number(_first(report['coastal_water_quality'],'salinity_psu','salinity'))} PSU</p><p><b>Specific conductance:</b> {_number(_first(report['coastal_water_quality'],'specific_conductance_us_cm','conductance'))} µS/cm</p></section>
<h2>Operational health</h2><section class='card'><p>Scheduler health: {html.escape(str(_first(report['scheduler_health'],'status') or 'Not available'))}</p><p>Alert severity: {html.escape(str(_first(report['scheduler_alert'],'severity') or 'Not available'))}</p></section>
<footer>Print this page to PDF only after both QA passes are complete and the publication status is authorized. Estimated reservoir response will change as new observations and forecasts arrive.</footer>
</main></body></html>"""


def build(repository_root: Path, config_path: Path, qa_passes_completed: int) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    inputs: dict[str, Any] = {}
    missing_inputs: list[str] = []
    for name, relative in config["inputs"].items():
        data = _read_json(repository_root / relative)
        inputs[name] = data or {}
        if data is None:
            missing_inputs.append(name)

    operations_cycle = inputs["operations_cycle"]
    hold_reasons: list[str] = []
    if qa_passes_completed < int(config.get("required_qa_passes", 2)):
        hold_reasons.append("Two-pass QA requirement has not been satisfied.")
    if isinstance(operations_cycle, dict) and operations_cycle:
        if operations_cycle.get("status") != "completed":
            hold_reasons.append("Latest operations cycle is not completed.")
        if operations_cycle.get("publication_authorized") is False:
            hold_reasons.append("Latest operations cycle has not authorized publication.")
    else:
        hold_reasons.append("Latest operations-cycle receipt is missing or unreadable.")

    essential = {"usgs_current", "reservoir_summary", "reservoir_water_budget"}
    for missing in sorted(essential.intersection(missing_inputs)):
        hold_reasons.append(f"Required input is missing: {missing}.")

    generated_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
    report = {
        "schema_version": 1,
        "build": "070",
        "report_title": config["report_title"],
        "generated_at": generated_at,
        "qa_passes_completed": qa_passes_completed,
        "publication_status": "authorized" if not hold_reasons else "pending_qa",
        "release_hold_reasons": hold_reasons,
        "missing_inputs": missing_inputs,
        "stations": _station_rows(inputs["usgs_current"], config["stations"]),
        "reservoirs": _reservoir_rows(
            inputs["reservoir_summary"],
            inputs["reservoir_water_budget"],
            inputs["reservoir_response"],
            config["reservoirs"],
        ),
        "coastal_water_quality": inputs["salt03"],
        "scheduler_health": inputs["scheduler_health"],
        "scheduler_alert": inputs["scheduler_alert"],
        "sources": {
            "usgs": "USGS Instantaneous Values API",
            "forecast_context": "NOAA/NWS NWPS",
            "reservoirs": "TWDB/Water Data for Texas and verified NRHIS reservoir inputs",
            "coastal": "SALT03 verified NRHIS input",
        },
    }

    outputs = config["outputs"]
    json_path = repository_root / outputs["json"]
    md_path = repository_root / outputs["markdown"]
    html_path = repository_root / outputs["html"]
    history_path = repository_root / outputs["history_jsonl"]
    receipt_path = repository_root / outputs["receipt"]
    markdown_text = _markdown(report)
    html_text = _html(report, markdown_text)
    _write(json_path, json.dumps(report, indent=2, sort_keys=True) + "\n")
    _write(md_path, markdown_text)
    _write(html_path, html_text)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with history_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(report, sort_keys=True) + "\n")
    receipt = {
        "schema_version": 1,
        "build": "070",
        "completed_at": generated_at,
        "status": "completed",
        "publication_status": report["publication_status"],
        "files": {
            "json": str(json_path),
            "markdown": str(md_path),
            "html": str(html_path),
            "history_jsonl": str(history_path),
        },
    }
    _write(receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    report["receipt_path"] = str(receipt_path)
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the NRHIS daily operations report")
    parser.add_argument("--repository-root", default=".")
    parser.add_argument("--config", default="config/nrhis/daily_operations_report.json")
    parser.add_argument("--qa-passes-completed", type=int, default=0)
    parser.add_argument("--fail-if-held", action="store_true")
    args = parser.parse_args()
    root = Path(args.repository_root).resolve()
    config_path = root / args.config
    report = build(root, config_path, args.qa_passes_completed)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if args.fail_if_held and report["publication_status"] != "authorized" else 0


if __name__ == "__main__":
    raise SystemExit(main())
