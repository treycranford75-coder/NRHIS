import json
from datetime import datetime, timezone
from pathlib import Path

from nrhis_harvest.usgs_basin_harvest import (
    append_deduplicated_jsonl,
    build_url,
    parse_usgs_payload,
)

FIXTURE = Path(__file__).parent / "fixtures" / "usgs_iv_build050.json"


def test_build_url_contains_sites_parameters_and_period():
    url = build_url(["08210000", "08211200"], ["00060", "00095"], "P2D")
    assert "sites=08210000%2C08211200" in url
    assert "parameterCd=00060%2C00095" in url
    assert "period=P2D" in url


def test_parser_normalizes_latest_values_and_estimated_tds():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    now = datetime(2026, 7, 20, 0, 30, tzinfo=timezone.utc)
    observations = parse_usgs_payload(payload, now=now, stale_minutes=90)
    assert len(observations) == 2
    discharge = next(item for item in observations if item.parameter_code == "00060")
    conductance = next(item for item in observations if item.parameter_code == "00095")
    assert discharge.value == 25.0
    assert discharge.provisional is True
    assert discharge.stale is False
    assert conductance.estimated_tds_mg_l == 1170.0


def test_history_append_is_duplicate_safe(tmp_path):
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    observations = parse_usgs_payload(
        payload, now=datetime(2026, 7, 20, 0, 30, tzinfo=timezone.utc), stale_minutes=90
    )
    path = tmp_path / "history.jsonl"
    assert append_deduplicated_jsonl(path, observations) == 2
    assert append_deduplicated_jsonl(path, observations) == 0
    assert len(path.read_text(encoding="utf-8").splitlines()) == 2
