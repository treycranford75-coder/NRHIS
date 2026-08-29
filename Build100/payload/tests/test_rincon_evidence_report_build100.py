from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path

from nrhis_analysis.rincon_evidence_report import build_rincon_evidence_report


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_inputs(tmp_path: Path) -> tuple[Path, Path]:
    summary = {
        "schema_version": 1,
        "build": "099",
        "site_no": "08211503",
        "requested_start": "2017-09-01",
        "requested_end": "2018-06-30",
        "count_reconciliation_identity_holds": True,
        "total_reverse_flow_volume_acft": 1014.211893,
        "observation_negative_interval_count_build097_semantics": 1293,
        "integrated_reverse_flow_interval_count_build098_semantics": 1133,
        "interval_count_difference": 160,
        "exact_zero_bridge_count": 160,
        "unintegrated_observation_run_count": 0,
        "sustained_reverse_intervals_ge_6h": 44,
        "sustained_reverse_volume_ge_6h_acft": 900.0,
        "multiday_reverse_intervals_ge_24h": 6,
        "multiday_reverse_volume_ge_24h_acft": 500.0,
        "critical_timeline": {
            "reverse_interval_ending_at_gap": {
                "event": "reverse_interval_ending_at_gap",
                "start": "2017-09-12T16:38:04.304933Z",
                "end": "2017-09-14T16:45:00Z",
                "status": "observable",
                "duration_hours": 48.115471,
                "reverse_volume_acft": 49.403734,
                "mean_reverse_discharge_cfs": -12.42397,
                "minimum_discharge_cfs": -24.9,
                "stage_records": "",
                "stage_coverage_ratio": "",
            },
            "material_discharge_gap": {
                "event": "material_discharge_gap",
                "start": "2017-09-14T17:00:00Z",
                "end": "2017-10-31T21:45:00Z",
                "status": "not_observable_from_discharge",
                "duration_hours": 1133.0,
                "reverse_volume_acft": "",
                "mean_reverse_discharge_cfs": "",
                "minimum_discharge_cfs": "",
                "stage_records": 4531,
                "stage_coverage_ratio": 1.0,
            },
            "first_reverse_interval_after_gap": {
                "event": "first_reverse_interval_after_gap",
                "start": "2017-10-31T23:00:00Z",
                "end": "2017-11-01T02:00:00Z",
                "status": "observable",
                "duration_hours": 3.0,
                "reverse_volume_acft": 1.5,
                "mean_reverse_discharge_cfs": -7.043804,
                "minimum_discharge_cfs": -12.7,
                "stage_records": "",
                "stage_coverage_ratio": "",
            },
            "terminal_discharge": {
                "event": "terminal_discharge_discontinuation",
                "start": "2018-05-12T13:45:00Z",
                "end": "2018-06-30T23:45:00Z",
                "status": "discharge_not_observable_after_terminal",
                "duration_hours": "",
                "reverse_volume_acft": "",
                "mean_reverse_discharge_cfs": 3.07,
                "minimum_discharge_cfs": "",
                "stage_records": 4401,
                "stage_coverage_ratio": "",
                "first_stage_after_terminal": "2018-05-14T22:45:00Z",
            },
        },
    }
    summary_path = tmp_path / "summary.json"
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    receipt = {
        "build": "099",
        "network_requests_made": 0,
        "summary_sha256": sha(summary_path),
        "source_csv_sha256": "a" * 64,
        "query_index_sha256": "b" * 64,
    }
    receipt_path = tmp_path / "receipt.json"
    receipt_path.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    return summary_path, receipt_path


def test_report_preserves_exact_pre_gap_evidence_and_limitations(tmp_path: Path) -> None:
    summary, receipt = write_inputs(tmp_path)
    out = tmp_path / "report"
    result = build_rincon_evidence_report(summary, receipt, out)
    text = (out / "NRHIS_Rincon_Evidence_Report.md").read_text(encoding="utf-8")
    assert "49.403734 acre-feet" in text
    assert "48.115 hours" in text
    assert "47 days" in text
    assert "4,531" in text
    assert "not observable from discharge and not estimated" in text
    assert "does not by itself establish the source, cause, or destination" in text
    assert result["network_requests_made"] == 0
    assert result["causation_claimed"] is False


def test_terminal_legacy_field_is_relabelled_as_terminal_discharge(tmp_path: Path) -> None:
    summary, receipt = write_inputs(tmp_path)
    out = tmp_path / "report"
    result = build_rincon_evidence_report(summary, receipt, out)
    assert result["terminal_discharge_cfs"] == 3.07
    text = (out / "NRHIS_Rincon_Evidence_Report.md").read_text(encoding="utf-8")
    assert "Final observed discharge: **3.070000 cfs**" in text
    assert "mean reverse discharge: **3.070000 cfs**" not in text.lower()


def test_evidence_table_and_hash_receipt_are_created(tmp_path: Path) -> None:
    summary, receipt = write_inputs(tmp_path)
    out = tmp_path / "report"
    result = build_rincon_evidence_report(summary, receipt, out)
    with (out / "evidence_findings.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 6
    assert rows[1]["value"] == "49.403734"
    assert rows[2]["status"] == "discharge_not_observable"
    assert sha(out / "NRHIS_Rincon_Evidence_Report.md") == result["report_markdown_sha256"]
    assert sha(out / "evidence_findings.csv") == result["evidence_findings_csv_sha256"]


def test_wrapper_and_cli_are_local_only() -> None:
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "scripts/generate_rincon_evidence_report.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    wrapper = Path("scripts/Generate-Rincon-Evidence-Report.ps1").read_text(encoding="utf-8")
    assert "local-only; zero USGS requests" in wrapper
