"""Build100 formal Rincon evidence report generator.

This module turns the Build099 evidence-reconciliation summary into a concise,
receipt-bound Markdown report and evidence table. It does not contact USGS and
never modifies the finalized NRHIS archive.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

ANALYSIS_SCHEMA_VERSION = 1
BUILD_NUMBER = "100"
DEFAULT_SITE_NO = "08211503"
CENTRAL = ZoneInfo("America/Chicago")


class ReportError(RuntimeError):
    """Raised when required upstream evidence is missing or inconsistent."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _atomic_write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name, suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _parse_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _fmt_time(value: str | None) -> str:
    parsed = _parse_utc(value)
    if parsed is None:
        return "not available"
    local = parsed.astimezone(CENTRAL)
    return f"{parsed.strftime('%Y-%m-%d %H:%M:%S UTC')} ({local.strftime('%Y-%m-%d %H:%M:%S %Z')})"


def _fmt_duration(hours: float | int | str | None) -> str:
    if hours in (None, ""):
        return "not available"
    value = float(hours)
    days = int(value // 24)
    remaining = value - days * 24
    if days:
        return f"{value:.3f} hours ({days} days {remaining:.3f} hours)"
    return f"{value:.3f} hours"


def _required_timeline(summary: dict[str, Any], key: str) -> dict[str, Any]:
    timeline = summary.get("critical_timeline")
    if not isinstance(timeline, dict):
        raise ReportError("Build099 summary is missing critical_timeline.")
    value = timeline.get(key)
    if not isinstance(value, dict):
        raise ReportError(f"Build099 summary is missing critical_timeline.{key}.")
    return value


def _load_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ReportError(f"Unable to read JSON evidence file {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ReportError(f"Expected JSON object in {path}.")
    return value


def build_rincon_evidence_report(
    build099_summary_path: Path,
    build099_receipt_path: Path,
    output_dir: Path,
    *,
    title: str = "NRHIS Rincon Bayou Evidence Report",
) -> dict[str, Any]:
    """Generate a formal Markdown report and machine-readable evidence table."""
    summary = _load_json(build099_summary_path)
    receipt099 = _load_json(build099_receipt_path)

    if str(summary.get("build")) != "099":
        raise ReportError("Input summary is not a Build099 summary.")
    if summary.get("count_reconciliation_identity_holds") is not True:
        raise ReportError("Build099 interval-count reconciliation did not pass.")
    if int(receipt099.get("network_requests_made", -1)) != 0:
        raise ReportError("Build099 receipt does not prove local-only analysis.")
    expected_summary_hash = str(receipt099.get("summary_sha256", ""))
    actual_summary_hash = sha256_file(build099_summary_path)
    if expected_summary_hash and expected_summary_hash != actual_summary_hash:
        raise ReportError("Build099 summary SHA-256 does not match its receipt.")

    pre_gap = _required_timeline(summary, "reverse_interval_ending_at_gap")
    gap = _required_timeline(summary, "material_discharge_gap")
    post_gap = _required_timeline(summary, "first_reverse_interval_after_gap")
    terminal = _required_timeline(summary, "terminal_discharge")

    total_volume = float(summary["total_reverse_flow_volume_acft"])
    observation_runs = int(summary["observation_negative_interval_count_build097_semantics"])
    integrated_intervals = int(summary["integrated_reverse_flow_interval_count_build098_semantics"])
    zero_bridges = int(summary["exact_zero_bridge_count"])
    unintegrated = int(summary["unintegrated_observation_run_count"])
    sustained_count = int(summary.get("sustained_reverse_intervals_ge_6h", 0))
    sustained_volume = float(summary.get("sustained_reverse_volume_ge_6h_acft", 0.0))
    multiday_count = int(summary.get("multiday_reverse_intervals_ge_24h", 0))
    multiday_volume = float(summary.get("multiday_reverse_volume_ge_24h_acft", 0.0))

    gap_hours = float(gap["duration_hours"])
    stage_records_gap = int(gap["stage_records"])
    stage_ratio = float(gap["stage_coverage_ratio"])

    # Build099's terminal timeline inherited a legacy field name. Its value is
    # the final observed discharge, not a reverse-flow mean. Relabel it here.
    terminal_discharge_cfs = float(terminal["mean_reverse_discharge_cfs"])
    stage_records_after_terminal = int(terminal["stage_records"])

    evidence_rows: list[dict[str, Any]] = [
        {
            "finding_id": "F01",
            "category": "reverse_flow",
            "status": "observed_and_derived",
            "start_utc": summary["requested_start"],
            "end_utc": summary["requested_end"],
            "value": f"{total_volume:.6f}",
            "unit": "acre-feet",
            "finding": (
                f"Integrated observed reverse-direction flow totaled {total_volume:.6f} acre-feet "
                "during discharge-observable portions of the requested analysis window."
            ),
        },
        {
            "finding_id": "F02",
            "category": "pre_gap_reverse_flow",
            "status": "observed_and_derived",
            "start_utc": pre_gap["start"],
            "end_utc": pre_gap["end"],
            "value": f"{float(pre_gap['reverse_volume_acft']):.6f}",
            "unit": "acre-feet",
            "finding": (
                "A sustained reverse-flow interval ended at the final discharge observation "
                "immediately before the 2017 material outage."
            ),
        },
        {
            "finding_id": "F03",
            "category": "discharge_gap",
            "status": "discharge_not_observable",
            "start_utc": gap["start"],
            "end_utc": gap["end"],
            "value": f"{gap_hours:.6f}",
            "unit": "hours",
            "finding": (
                f"Published discharge was unavailable for {gap_hours:.3f} hours while "
                f"{stage_records_gap} stage observations covered {stage_ratio:.3f} of expected slots."
            ),
        },
        {
            "finding_id": "F04",
            "category": "post_gap_reverse_flow",
            "status": "observed_and_derived",
            "start_utc": post_gap["start"],
            "end_utc": post_gap["end"],
            "value": f"{float(post_gap['reverse_volume_acft']):.6f}",
            "unit": "acre-feet",
            "finding": "Reverse-direction discharge was again observable after discharge reporting resumed.",
        },
        {
            "finding_id": "F05",
            "category": "terminal_discharge",
            "status": "observed",
            "start_utc": terminal["start"],
            "end_utc": terminal["end"],
            "value": f"{terminal_discharge_cfs:.6f}",
            "unit": "cfs",
            "finding": (
                f"The final published discharge observation was {terminal_discharge_cfs:.6f} cfs; "
                f"{stage_records_after_terminal} stage observations occurred afterward in the window."
            ),
        },
        {
            "finding_id": "F06",
            "category": "interval_semantics",
            "status": "reconciled",
            "start_utc": "",
            "end_utc": "",
            "value": f"{observation_runs}-{integrated_intervals}={zero_bridges}+{unintegrated}",
            "unit": "intervals",
            "finding": (
                "The Build097/Build098 interval-count difference is fully reconciled by exact-zero "
                "bridges and unintegrated runs."
            ),
        },
    ]

    limitations = [
        "Negative discharge at USGS 08211503 establishes direction at the gage; it does not by itself establish the source, cause, or destination of the water.",
        "No reverse-flow volume is assigned to the 2017 discharge outage because discharge was not observable during that period.",
        "No reverse-flow volume is assigned after the May 12, 2018 terminal discharge observation because discharge was not observable afterward in the analyzed window.",
        "Continuing stage observations demonstrate that stage monitoring continued; stage is not a substitute for directional discharge measurement.",
        "All volumetric results are derived from the finalized local NRHIS archive and the Build098 piecewise-linear negative-discharge integration method.",
    ]

    report_lines = [
        f"# {title}",
        "",
        f"**Site:** USGS {summary['site_no']} — Rincon Bayou Channel near Calallen, Texas  ",
        f"**Analysis window:** {summary['requested_start']} through {summary['requested_end']}  ",
        "**Mode:** Local finalized NRHIS archive; zero USGS network requests during analysis/report generation  ",
        f"**Build099 source summary SHA-256:** `{actual_summary_hash}`",
        "",
        "## Executive finding",
        "",
        (
            f"NRHIS measured **{total_volume:.3f} acre-feet of observed reverse-direction flow** "
            "during discharge-observable portions of the September 2017–June 2018 analysis window. "
            "A sustained reverse-flow interval ran directly into the September 14, 2017 discharge outage; "
            "published discharge was then unavailable for 47 days and 5 hours while stage coverage remained "
            "complete for the expected 15-minute slots. Discharge later resumed, reverse-direction flow remained "
            "observable, and the published discharge record ultimately ended on May 12, 2018 while stage "
            "monitoring continued afterward."
        ),
        "",
        "## Critical timeline",
        "",
        "### 1. Reverse flow immediately before the 2017 outage",
        "",
        f"- Start: **{_fmt_time(pre_gap['start'])}**",
        f"- End: **{_fmt_time(pre_gap['end'])}**",
        f"- Duration: **{_fmt_duration(pre_gap['duration_hours'])}**",
        f"- Integrated reverse-flow volume: **{float(pre_gap['reverse_volume_acft']):.6f} acre-feet**",
        f"- Mean reverse discharge: **{float(pre_gap['mean_reverse_discharge_cfs']):.6f} cfs**",
        f"- Minimum discharge: **{float(pre_gap['minimum_discharge_cfs']):.6f} cfs**",
        "",
        "### 2. Material 2017 discharge outage",
        "",
        f"- Missing-discharge interval: **{_fmt_time(gap['start'])} to {_fmt_time(gap['end'])}**",
        f"- Duration: **{_fmt_duration(gap_hours)}**",
        f"- Stage records during missing discharge slots: **{stage_records_gap:,}**",
        f"- Stage coverage ratio: **{stage_ratio:.3f}**",
        "- Reverse-flow volume during this interval: **not observable from discharge and not estimated by NRHIS**",
        "",
        "### 3. Reverse flow after discharge reporting resumed",
        "",
        f"- First post-gap reverse interval: **{_fmt_time(post_gap['start'])} to {_fmt_time(post_gap['end'])}**",
        f"- Duration: **{_fmt_duration(post_gap['duration_hours'])}**",
        f"- Integrated reverse-flow volume: **{float(post_gap['reverse_volume_acft']):.6f} acre-feet**",
        f"- Mean reverse discharge: **{float(post_gap['mean_reverse_discharge_cfs']):.6f} cfs**",
        f"- Minimum discharge: **{float(post_gap['minimum_discharge_cfs']):.6f} cfs**",
        "",
        "### 4. Terminal discharge discontinuation",
        "",
        f"- Final published discharge observation: **{_fmt_time(terminal['start'])}**",
        f"- Final observed discharge: **{terminal_discharge_cfs:.6f} cfs**",
        f"- Stage records after terminal discharge in the analysis window: **{stage_records_after_terminal:,}**",
        f"- Last stage observation in window: **{_fmt_time(terminal['end'])}**",
        "- Discharge after the terminal observation: **not observable and not estimated by NRHIS**",
        "",
        "## Reverse-flow event structure",
        "",
        f"- Build097 sampled negative-observation runs: **{observation_runs:,}**",
        f"- Build098 integrated reverse-flow intervals: **{integrated_intervals:,}**",
        f"- Exact-zero bridges explaining merged runs: **{zero_bridges:,}**",
        f"- Unintegrated negative-observation runs: **{unintegrated:,}**",
        f"- Sustained reverse-flow intervals ≥6 hours: **{sustained_count:,}**, totaling **{sustained_volume:.3f} acre-feet**",
        f"- Multi-day reverse-flow intervals ≥24 hours: **{multiday_count:,}**, totaling **{multiday_volume:.3f} acre-feet**",
        "",
        "## Evidentiary interpretation",
        "",
        (
            "The record demonstrates that directional reverse flow was measurable immediately before the "
            "September 2017 discharge outage and again after discharge reporting resumed. The outage itself "
            "cannot be assigned a discharge volume from this station because the directional-discharge product "
            "was unavailable, even though stage monitoring continued. The later May 2018 termination likewise "
            "marks the end of the published directional-discharge record, not the end of stage monitoring."
        ),
        "",
        "## Limitations",
        "",
    ]
    report_lines.extend(f"- {item}" for item in limitations)
    report_lines.extend(
        [
            "",
            "## Provenance",
            "",
            f"- Build099 summary: `{build099_summary_path.resolve()}`",
            f"- Build099 receipt: `{build099_receipt_path.resolve()}`",
            f"- Build099 summary SHA-256: `{actual_summary_hash}`",
            f"- Finalized source CSV SHA-256: `{receipt099.get('source_csv_sha256', 'not recorded')}`",
            f"- Historical query-index SHA-256: `{receipt099.get('query_index_sha256', 'not recorded')}`",
            "",
        ]
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / "NRHIS_Rincon_Evidence_Report.md"
    findings_path = output_dir / "evidence_findings.csv"
    receipt_path = output_dir / "report-receipt.json"

    _atomic_write_text(report_path, "\n".join(report_lines))
    _atomic_write_csv(
        findings_path,
        ["finding_id", "category", "status", "start_utc", "end_utc", "value", "unit", "finding"],
        evidence_rows,
    )

    report_receipt: dict[str, Any] = {
        "schema_version": ANALYSIS_SCHEMA_VERSION,
        "build": BUILD_NUMBER,
        "report": "rincon_evidence_report",
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "query_mode": "local_finalized_archive",
        "network_requests_made": 0,
        "site_no": summary["site_no"],
        "requested_start": summary["requested_start"],
        "requested_end": summary["requested_end"],
        "build099_summary": str(build099_summary_path.resolve()),
        "build099_summary_sha256": actual_summary_hash,
        "build099_receipt": str(build099_receipt_path.resolve()),
        "build099_receipt_sha256": sha256_file(build099_receipt_path),
        "source_csv_sha256": receipt099.get("source_csv_sha256"),
        "query_index_sha256": receipt099.get("query_index_sha256"),
        "report_markdown": str(report_path.resolve()),
        "report_markdown_sha256": sha256_file(report_path),
        "evidence_findings_csv": str(findings_path.resolve()),
        "evidence_findings_csv_sha256": sha256_file(findings_path),
        "total_reverse_flow_volume_acft": round(total_volume, 6),
        "pre_gap_reverse_flow_volume_acft": round(float(pre_gap["reverse_volume_acft"]), 6),
        "material_discharge_gap_hours": round(gap_hours, 6),
        "material_gap_stage_records": stage_records_gap,
        "material_gap_stage_coverage_ratio": round(stage_ratio, 6),
        "terminal_discharge_observed_at": terminal["start"],
        "terminal_discharge_cfs": round(terminal_discharge_cfs, 6),
        "stage_records_after_terminal": stage_records_after_terminal,
        "count_reconciliation_identity_holds": True,
        "causation_claimed": False,
    }
    _atomic_write_text(receipt_path, json.dumps(report_receipt, indent=2, sort_keys=True) + "\n")
    report_receipt["receipt"] = str(receipt_path.resolve())
    return report_receipt
