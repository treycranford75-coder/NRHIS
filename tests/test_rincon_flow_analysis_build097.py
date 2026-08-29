from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from nrhis_analysis.rincon_flow_analysis import analyze_rincon_flow
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


def write_fixture(path: Path) -> None:
    start = datetime(2017, 9, 14, 0, 0, tzinfo=timezone.utc)
    end = datetime(2017, 9, 17, 0, 0, tzinfo=timezone.utc)
    gap_start = datetime(2017, 9, 14, 12, 0, tzinfo=timezone.utc)
    gap_end = datetime(2017, 9, 15, 12, 0, tzinfo=timezone.utc)
    terminal = datetime(2017, 9, 15, 18, 0, tzinfo=timezone.utc)

    rows: list[dict[str, str]] = []
    current = start
    while current < end:
        rows.append(
            {
                "estimated_tds_mg_l": "",
                "observed_at": iso_z(current),
                "parameter_code": "00065",
                "parameter_name": "gage_height",
                "provisional": "false",
                "qualifiers": '["A"]',
                "site_name": "Rincon Bayou Channel near Calallen, TX",
                "site_no": "08211503",
                "source": "USGS Instantaneous Values API",
                "unit": "ft",
                "value": "1.5",
            }
        )
        if current <= terminal and not (gap_start <= current < gap_end):
            discharge = "-8.0" if current < start + timedelta(hours=2) else "4.0"
            rows.append(
                {
                    "estimated_tds_mg_l": "",
                    "observed_at": iso_z(current),
                    "parameter_code": "00060",
                    "parameter_name": "discharge",
                    "provisional": "false",
                    "qualifiers": '["A"]',
                    "site_name": "Rincon Bayou Channel near Calallen, TX",
                    "site_no": "08211503",
                    "source": "USGS Instantaneous Values API",
                    "unit": "ft3/s",
                    "value": discharge,
                }
            )
        current += timedelta(minutes=15)

    rows.sort(key=lambda row: (row["observed_at"], row["site_no"], row["parameter_code"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def test_detects_gap_stage_continuity_terminal_and_negative_flow(tmp_path: Path) -> None:
    csv_path = tmp_path / "history.csv"
    index_path = tmp_path / "index.json"
    output_dir = tmp_path / "analysis"
    write_fixture(csv_path)
    build_sparse_index(csv_path, index_path, stride_rows=20)

    receipt = analyze_rincon_flow(
        csv_path,
        index_path,
        output_dir,
        start="2017-09-14",
        end="2017-09-16",
        gap_hours=6,
        stage_continuity_ratio=0.8,
    )

    assert receipt["network_requests_made"] == 0
    assert receipt["discharge_gap_count"] == 1
    assert receipt["negative_flow_interval_count"] == 1
    assert receipt["terminal_stage_continued_after_discharge"] is True
    assert receipt["last_discharge_observed_at"] == "2017-09-15T18:00:00Z"
    assert receipt["last_stage_observed_at"] == "2017-09-16T23:45:00Z"

    summary = json.loads((output_dir / "rincon_flow_summary.json").read_text(encoding="utf-8"))
    assert summary["discharge_gaps_with_stage_continuity"] == 1
    assert summary["terminal_stage_continued_after_discharge"] is True
    assert summary["stage_records_after_last_discharge"] > 0
    assert summary["longest_discharge_gap"]["stage_continued"] is True
    assert summary["longest_discharge_gap"]["stage_coverage_ratio"] >= 0.95

    with (output_dir / "negative_flow_intervals.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert float(rows[0]["minimum_discharge_cfs"]) == -8.0
    assert int(rows[0]["observation_count"]) == 8


def test_receipt_hashes_outputs_and_source(tmp_path: Path) -> None:
    csv_path = tmp_path / "history.csv"
    index_path = tmp_path / "index.json"
    output_dir = tmp_path / "analysis"
    write_fixture(csv_path)
    index = build_sparse_index(csv_path, index_path, stride_rows=20)

    receipt = analyze_rincon_flow(
        csv_path,
        index_path,
        output_dir,
        start="2017-09-14",
        end="2017-09-16",
        gap_hours=6,
    )

    assert receipt["source_csv_sha256"] == index["source_csv_sha256"]
    assert len(receipt["summary_sha256"]) == 64
    assert len(receipt["discharge_gaps_csv_sha256"]) == 64
    assert len(receipt["negative_flow_intervals_csv_sha256"]) == 64
    assert Path(receipt["receipt"]).is_file()


def test_cli_and_wrapper_are_local_only() -> None:
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "scripts/analyze_rincon_flow.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Analyze Rincon Bayou discharge gaps" in result.stdout

    wrapper = Path("scripts/Analyze-Rincon-Flow.ps1").read_text(encoding="utf-8")
    assert "local-only; zero USGS requests" in wrapper
    assert "data/nrhis/normalized/usgs_historical_observations.csv" in wrapper
    assert "data/nrhis/backfill/usgs_history_query_index.json" in wrapper
