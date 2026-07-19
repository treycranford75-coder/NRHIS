import json
from datetime import date
from pathlib import Path

from nrhis_harvest.usgs_historical_backfill import (
    append_deduplicated,
    build_url,
    iter_date_chunks,
    parse_payload,
    rebuild_csv,
)

FIXTURE = Path(__file__).parent / "fixtures" / "usgs_iv_build050.json"


def test_date_chunks_are_complete_and_nonoverlapping():
    chunks = list(iter_date_chunks(date(2024, 2, 1), date(2024, 2, 15), 7))
    assert chunks == [
        (date(2024, 2, 1), date(2024, 2, 7)),
        (date(2024, 2, 8), date(2024, 2, 14)),
        (date(2024, 2, 15), date(2024, 2, 15)),
    ]


def test_historical_url_uses_explicit_date_range():
    url = build_url(["08210000"], ["00060"], date(2024, 2, 1), date(2024, 2, 7))
    assert "startDT=2024-02-01" in url
    assert "endDT=2024-02-07" in url
    assert "sites=08210000" in url


def test_historical_parser_keeps_all_values_and_tds_estimate(tmp_path):
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    records = parse_payload(payload)
    assert len(records) == 2
    conductance = next(row for row in records if row.parameter_code == "00095")
    assert conductance.estimated_tds_mg_l == 1170.0
    history = tmp_path / "history.jsonl"
    assert append_deduplicated(history, records) == 2
    assert append_deduplicated(history, records) == 0
    csv_path = tmp_path / "history.csv"
    assert rebuild_csv(history, csv_path) == 2
    assert "estimated_tds_mg_l" in csv_path.read_text(encoding="utf-8").splitlines()[0]
