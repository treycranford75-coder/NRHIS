import json
from datetime import date
from pathlib import Path

from nrhis_harvest.models import Station
from nrhis_harvest.usgs import build_query, normalize


def station() -> Station:
    return Station(
        station_id="USGS-08211500",
        agency="USGS",
        agency_id="08211500",
        name="Nueces River at Calallen, Texas",
        waterbody="Nueces River",
        role="primary",
        status="active",
        parameters=("discharge", "gage_height"),
    )


def test_build_query_is_deterministic() -> None:
    query = build_query([station()], date(2026, 7, 16), date(2026, 7, 17))
    assert query["sites"] == "08211500"
    assert query["parameterCd"] == "00060,00065"
    assert query["startDT"] == "2026-07-16"


def test_normalize_sample_fixture() -> None:
    payload = json.loads(Path("tests/fixtures/usgs_iv_sample.json").read_text(encoding="utf-8"))
    rows = normalize(payload, [station()])
    assert len(rows) == 2
    assert rows[0]["station_id"] == "USGS-08211500"
    assert rows[0]["parameter"] == "discharge"
    assert rows[0]["value"] == 25.0
    assert rows[0]["qualifiers"] == "P"
