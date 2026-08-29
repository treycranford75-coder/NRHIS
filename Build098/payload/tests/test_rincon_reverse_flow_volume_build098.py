from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from nrhis_analysis.rincon_reverse_flow_volume import analyze_rincon_reverse_flow
from nrhis_analysis.usgs_history_query import build_sparse_index

FIELDS = [
    "estimated_tds_mg_l",
    "observed_at",
    "parameter_code",
    "parameter_name",
    "provisional",
    "qualifiers",
    "site_name",
    "site_no",
    "source",
    "unit",
    "value",
]


def iso_z(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def add_row(rows: list[dict[str, str]], when: datetime, parameter: str, value: float) -> None:
    rows.append(
        {
            "estimated_tds_mg_l": "",
            "observed_at": iso_z(when),
            "parameter_code": parameter,
            "parameter_name": "discharge" if parameter == "00060" else "gage_height",
            "provisional": "false",
            "qualifiers": '["A"]',
            "site_name": "Rincon Bayou Channel near Calallen, TX",
            "site_no": "08211503",
            "source": "USGS Instantaneous Values API",
            "unit": "ft3/s" if parameter == "00060" else "ft",
            "value": str(value),
        }
    )


def write_fixture(path: Path) -> None:
    # Four days at 15-minute cadence. Discharge has a one-day material gap and
    # terminates before stage. A known -10 cfs one-hour plateau provides a stable
    # integration target of 10 cfs-hours / 12.1 ~= 0.826446 acre-feet.
    start = datetime(2017, 9, 1, tzinfo=timezone.utc)
    end = datetime(2017, 9, 5, tzinfo=timezone.utc)
    gap_start = datetime(2017, 9, 2, tzinfo=timezone.utc)
    gap_end = datetime(2017, 9, 3, tzinfo=timezone.utc)
    terminal = datetime(2017, 9, 4, 12, tzinfo=timezone.utc)
    neg_start = datetime(2017, 9, 1, 6, tzinfo=timezone.utc)
    neg_end = datetime(2017, 9, 1, 7, tzinfo=timezone.utc)
    rows: list[dict[str, str]] = []
    current = start
    while current < end:
        add_row(rows, current, "00065", 1.5)
        if current <= terminal and not (gap_start <= current < gap_end):
            q = -10.0 if neg_start <= current <= neg_end else 5.0
            add_row(rows, current, "00060", q)
        current += timedelta(minutes=15)
    rows.sort(key=lambda row: (row["observed_at"], row["site_no"], row["parameter_code"]))
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def test_integrates_reverse_volume_and_marks_unobservable_phases(tmp_path: Path) -> None:
    csv_path = tmp_path / "history.csv"
    index_path = tmp_path / "index.json"
    output_dir = tmp_path / "analysis"
    write_fixture(csv_path)
    build_sparse_index(csv_path, index_path, stride_rows=20)

    receipt = analyze_rincon_reverse_flow(
        csv_path,
        index_path,
        output_dir,
        start="2017-09-01",
        end="2017-09-04",
        gap_hours=12,
    )
    assert receipt["network_requests_made"] == 0
    assert receipt["reverse_flow_interval_count"] >= 1
    assert receipt["total_reverse_flow_volume_acft"] > 0

    summary = json.loads((output_dir / "rincon_reverse_flow_summary.json").read_text(encoding="utf-8"))
    assert summary["integration_method"] == "piecewise_linear_negative_portion"
    assert summary["longest_material_discharge_gap"]["missing_slots"] > 0
    phases = {row["phase"]: row for row in summary["phase_summary"]}
    monthly_total = sum(float(row["reverse_volume_acft"]) for row in summary["monthly_reverse_flow"])
    observable_phase_total = sum(
        float(row["reverse_volume_acft"])
        for row in summary["phase_summary"]
        if row["status"] == "observable"
    )
    assert monthly_total == pytest.approx(summary["total_reverse_flow_volume_acft"], rel=1e-5)
    assert observable_phase_total == pytest.approx(summary["total_reverse_flow_volume_acft"], rel=1e-5)
    assert phases["discharge_gap"]["status"] == "not_observable_from_discharge"
    assert phases["discharge_gap"]["reverse_volume_acft"] == ""
    assert phases["post_terminal"]["status"] == "not_observable_from_discharge"
    assert phases["post_terminal"]["stage_record_count"] > 0


def test_piecewise_linear_zero_crossing_volume(tmp_path: Path) -> None:
    # Two 15-minute points: -10 to +10 cfs. Linear zero crossing occurs halfway,
    # so reverse volume is a triangle: 0.5 * 10 cfs * 450 s / 43560.
    csv_path = tmp_path / "history.csv"
    index_path = tmp_path / "index.json"
    output_dir = tmp_path / "analysis"
    t0 = datetime(2017, 1, 1, tzinfo=timezone.utc)
    rows: list[dict[str, str]] = []
    add_row(rows, t0, "00060", -10.0)
    add_row(rows, t0 + timedelta(minutes=15), "00060", 10.0)
    add_row(rows, t0, "00065", 1.0)
    add_row(rows, t0 + timedelta(minutes=15), "00065", 1.0)
    rows.sort(key=lambda row: (row["observed_at"], row["site_no"], row["parameter_code"]))
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    build_sparse_index(csv_path, index_path, stride_rows=2)
    receipt = analyze_rincon_reverse_flow(
        csv_path,
        index_path,
        output_dir,
        start="2017-01-01",
        end="2017-01-01",
        gap_hours=24,
    )
    expected = 0.5 * 10.0 * 450.0 / 43560.0
    assert receipt["total_reverse_flow_volume_acft"] == pytest.approx(expected, rel=1e-5)


def test_receipt_hashes_all_outputs(tmp_path: Path) -> None:
    csv_path = tmp_path / "history.csv"
    index_path = tmp_path / "index.json"
    output_dir = tmp_path / "analysis"
    write_fixture(csv_path)
    build_sparse_index(csv_path, index_path, stride_rows=20)
    receipt = analyze_rincon_reverse_flow(
        csv_path,
        index_path,
        output_dir,
        start="2017-09-01",
        end="2017-09-04",
        gap_hours=12,
    )
    for key in (
        "summary_sha256",
        "reverse_flow_intervals_csv_sha256",
        "duration_classes_csv_sha256",
        "monthly_reverse_flow_csv_sha256",
        "phase_summary_csv_sha256",
    ):
        assert len(receipt[key]) == 64
    assert Path(receipt["receipt"]).is_file()


def test_cli_and_wrapper_are_local_only() -> None:
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "scripts/analyze_rincon_reverse_flow.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "reverse-direction discharge" in result.stdout
    wrapper = Path("scripts/Analyze-Rincon-ReverseFlow.ps1").read_text(encoding="utf-8")
    assert "local-only; zero USGS requests" in wrapper
    assert "piecewise-linear integration" in wrapper
