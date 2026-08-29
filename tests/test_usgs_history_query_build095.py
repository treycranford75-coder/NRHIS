from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest

from nrhis_analysis import usgs_history_query as query


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


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def _row(when: str, site: str, parameter: str, value: str) -> dict[str, str]:
    return {
        "estimated_tds_mg_l": "",
        "observed_at": when,
        "parameter_code": parameter,
        "parameter_name": "discharge" if parameter == "00060" else "gage_height",
        "provisional": "False",
        "qualifiers": "A",
        "site_name": f"Site {site}",
        "site_no": site,
        "source": "USGS Instantaneous Values API",
        "unit": "ft3/s" if parameter == "00060" else "ft",
        "value": value,
    }


def test_sparse_index_and_window_query_are_bounded_and_filtered(tmp_path: Path) -> None:
    csv_path = tmp_path / "history.csv"
    index_path = tmp_path / "index.json"
    _write_csv(
        csv_path,
        [
            _row("2018-05-12T13:30:00Z", "08211503", "00060", "2.68"),
            _row("2018-05-12T13:45:00Z", "08211503", "00060", "3.07"),
            _row("2018-05-12T13:45:00Z", "08211503", "00065", "1.85"),
            _row("2018-05-13T00:00:00Z", "08211500", "00060", "20"),
        ],
    )
    index = query.build_sparse_index(csv_path, index_path, stride_rows=2)
    assert index["total_rows"] == 4
    assert len(index["entries"]) == 2

    rows = list(
        query.query_history(
            csv_path,
            index_path,
            start="2018-05-12",
            end="2018-05-12",
            site_nos=["08211503"],
            parameter_codes=["00060"],
        )
    )
    assert [row["observed_at"] for row in rows] == [
        "2018-05-12T13:30:00Z",
        "2018-05-12T13:45:00Z",
    ]
    assert rows[-1]["value"] == "3.07"


def test_sparse_index_rejects_unsorted_final_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "history.csv"
    index_path = tmp_path / "index.json"
    _write_csv(
        csv_path,
        [
            _row("2020-01-02T00:00:00Z", "A", "00060", "2"),
            _row("2020-01-01T00:00:00Z", "A", "00060", "1"),
        ],
    )
    with pytest.raises(query.QueryError, match="not globally sorted"):
        query.build_sparse_index(csv_path, index_path, stride_rows=1)


def test_query_bundle_is_network_free_and_hash_bound(tmp_path: Path) -> None:
    csv_path = tmp_path / "history.csv"
    index_path = tmp_path / "index.json"
    output = tmp_path / "bundle"
    _write_csv(
        csv_path,
        [
            _row("2017-09-14T16:45:00Z", "08211503", "00060", "-8.89"),
            _row("2017-10-31T21:45:00Z", "08211503", "00060", "6.75"),
        ],
    )
    index = query.build_sparse_index(csv_path, index_path, stride_rows=1)
    receipt = query.write_query_bundle(
        csv_path,
        index_path,
        output,
        start="2017-09-01",
        end="2017-11-01",
        site_nos=["08211503"],
        parameter_codes=["00060"],
    )
    assert receipt["network_requests_made"] == 0
    assert receipt["result_count"] == 2
    assert receipt["source_csv_sha256"] == index["source_csv_sha256"]
    assert Path(receipt["output_csv"]).is_file()
    saved = json.loads(Path(receipt["receipt"]).read_text(encoding="utf-8"))
    assert saved["build"] == "095"


def test_index_detects_changed_source_size(tmp_path: Path) -> None:
    csv_path = tmp_path / "history.csv"
    index_path = tmp_path / "index.json"
    _write_csv(csv_path, [_row("2020-01-01T00:00:00Z", "A", "00060", "1")])
    query.build_sparse_index(csv_path, index_path, stride_rows=1)
    with csv_path.open("a", encoding="utf-8") as handle:
        handle.write("changed\n")
    with pytest.raises(query.QueryError, match="size changed"):
        query.load_sparse_index(index_path, csv_path)


def test_powershell_wrapper_is_explicitly_local_only() -> None:
    script = Path("scripts/Query-USGS-History.ps1").read_text(encoding="utf-8")
    assert "query_usgs_history.py" in script
    assert "zero USGS requests" in script
    assert "waterservices.usgs.gov" not in script
