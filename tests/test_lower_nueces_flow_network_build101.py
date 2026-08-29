from __future__ import annotations

import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from nrhis_analysis.lower_nueces_flow_network import analyze_lower_nueces_flow_network
from nrhis_analysis.usgs_history_query import build_sparse_index


def _iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _write_csv(path: Path, lag_hours: int = 3) -> None:
    fields = [
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
    start = datetime(2018, 1, 1, tzinfo=timezone.utc)
    rows: list[dict[str, str]] = []
    # Forty-eight hours, four samples/hour. Downstream is a 3-hour-delayed copy.
    for quarter in range(48 * 4):
        observed = start + timedelta(minutes=15 * quarter)
        hour = quarter // 4
        upstream = float((hour % 13) * 2 + (hour // 13))
        rows.append(_row(observed, "08211000", upstream))
        rows.append(_row(observed, "08211200", upstream + 5.0))
        if hour >= lag_hours:
            source_hour = hour - lag_hours
            delayed = float((source_hour % 13) * 2 + (source_hour // 13))
            rows.append(_row(observed, "08211500", delayed))
    rows.sort(key=lambda row: (row["observed_at"], row["site_no"], row["parameter_code"]))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def _row(observed: datetime, site: str, value: float) -> dict[str, str]:
    return {
        "estimated_tds_mg_l": "",
        "observed_at": _iso(observed),
        "parameter_code": "00060",
        "parameter_name": "discharge",
        "provisional": "false",
        "qualifiers": "A",
        "site_name": site,
        "site_no": site,
        "source": "test",
        "unit": "ft3/s",
        "value": str(value),
    }


def test_network_analysis_recovers_known_mathis_calallen_lag(tmp_path: Path) -> None:
    csv_path = tmp_path / "history.csv"
    index_path = tmp_path / "index.json"
    _write_csv(csv_path, lag_hours=3)
    build_sparse_index(csv_path, index_path, stride_rows=25)
    result = analyze_lower_nueces_flow_network(
        csv_path,
        index_path,
        tmp_path / "out",
        start="2018-01-01",
        end="2018-01-02",
        min_observations_per_hour=2,
        max_lag_hours=6,
        min_paired_hours=10,
    )
    best = {row["pair"]: row for row in result["best_lag_results"]}
    assert best["Mathis_to_Calallen"]["lag_hours"] == 3
    assert float(best["Mathis_to_Calallen"]["pearson_r"]) > 0.999
    assert result["network_requests_made"] == 0
    assert result["interpretation"]["physical_travel_time_claim"] is False


def test_outputs_are_hash_bound_and_hourly_coverage_is_retained(tmp_path: Path) -> None:
    csv_path = tmp_path / "history.csv"
    index_path = tmp_path / "index.json"
    _write_csv(csv_path)
    build_sparse_index(csv_path, index_path, stride_rows=31)
    result = analyze_lower_nueces_flow_network(
        csv_path,
        index_path,
        tmp_path / "out",
        start="2018-01-01",
        end="2018-01-02",
        max_lag_hours=4,
        min_paired_hours=10,
    )
    assert result["station_coverage"]["08211000"]["hourly_bins_retained"] == 48
    assert Path(result["hourly_discharge_csv"]).is_file()
    assert len(result["hourly_discharge_csv_sha256"]) == 64
    receipt = json.loads(Path(result["receipt"]).read_text(encoding="utf-8"))
    assert receipt["network_requests_made"] == 0
    assert receipt["causation_claimed"] is False


def test_cli_and_wrapper_are_local_only() -> None:
    wrapper = Path("scripts/Analyze-LowerNueces-FlowNetwork.ps1").read_text(encoding="utf-8")
    cli = Path("scripts/analyze_lower_nueces_flow_network.py").read_text(encoding="utf-8")
    assert "local-only; zero USGS requests" in wrapper
    assert "requests" not in cli
    assert "physical travel time" in wrapper
