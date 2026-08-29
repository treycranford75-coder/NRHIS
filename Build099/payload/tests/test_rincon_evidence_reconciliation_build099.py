from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from nrhis_analysis.rincon_evidence_reconciliation import (
    _exact_zero_bridges,
    _observation_negative_runs,
    _reconcile,
    analyze_rincon_evidence_reconciliation,
)
from nrhis_analysis.rincon_reverse_flow_volume import Point, _integrate_reverse_flow
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


def test_exact_zero_bridge_explains_one_interval_difference() -> None:
    t0 = datetime(2017, 1, 1, tzinfo=timezone.utc)
    points = [
        Point(t0, -2.0),
        Point(t0 + timedelta(minutes=15), 0.0),
        Point(t0 + timedelta(minutes=30), -3.0),
        Point(t0 + timedelta(minutes=45), 2.0),
    ]
    cadence = timedelta(minutes=15)
    observation_runs = _observation_negative_runs(points, cadence=cadence)
    integrated, _ = _integrate_reverse_flow(points, cadence=cadence)
    rows, orphan_rows, merged_excess = _reconcile(observation_runs, integrated)
    assert len(observation_runs) == 2
    assert len(integrated) == 1
    assert merged_excess == 1
    assert not orphan_rows
    assert rows[0]["observation_run_count"] == 2
    assert len(_exact_zero_bridges(points, cadence=cadence)) == 1


def test_full_analysis_reconciles_and_extracts_gap_timeline(tmp_path: Path) -> None:
    csv_path = tmp_path / "history.csv"
    index_path = tmp_path / "index.json"
    output_dir = tmp_path / "analysis"
    start = datetime(2017, 9, 1, tzinfo=timezone.utc)
    rows: list[dict[str, str]] = []
    # Stage remains continuous for three days. Discharge has a material one-day
    # gap. The negative run immediately before the gap must be selected as a
    # critical evidence event.
    for step in range(3 * 24 * 4):
        when = start + timedelta(minutes=15 * step)
        add_row(rows, when, "00065", 1.5)
        if datetime(2017, 9, 2, tzinfo=timezone.utc) <= when < datetime(
            2017, 9, 3, tzinfo=timezone.utc
        ):
            continue
        if when < datetime(2017, 9, 2, tzinfo=timezone.utc):
            q = -5.0 if when >= datetime(2017, 9, 1, 18, tzinfo=timezone.utc) else 4.0
        else:
            q = -2.0 if when >= datetime(2017, 9, 3, 6, tzinfo=timezone.utc) else 3.0
        add_row(rows, when, "00060", q)
    rows.sort(key=lambda row: (row["observed_at"], row["site_no"], row["parameter_code"]))
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    build_sparse_index(csv_path, index_path, stride_rows=20)
    receipt = analyze_rincon_evidence_reconciliation(
        csv_path,
        index_path,
        output_dir,
        start="2017-09-01",
        end="2017-09-03",
        gap_hours=12,
    )
    assert receipt["network_requests_made"] == 0
    assert receipt["count_reconciliation_identity_holds"] is True
    summary = json.loads(
        (output_dir / "rincon_evidence_reconciliation_summary.json").read_text(encoding="utf-8")
    )
    assert summary["critical_timeline"]["material_discharge_gap"]["stage_coverage_ratio"] == 1.0
    assert summary["critical_timeline"]["reverse_interval_ending_at_gap"]["reverse_volume_acft"] > 0
    assert summary["count_reconciliation_identity_holds"] is True


def test_wrapper_and_cli_are_local_only() -> None:
    import subprocess
    import sys

    result = subprocess.run(
        [sys.executable, "scripts/analyze_rincon_evidence_reconciliation.py", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "Reconcile Build097" in result.stdout
    wrapper = Path("scripts/Analyze-Rincon-Evidence.ps1").read_text(encoding="utf-8")
    assert "local-only; zero USGS requests" in wrapper
