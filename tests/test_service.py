import csv
import json
from datetime import UTC, date, datetime
from pathlib import Path

from nrhis_harvest.service import harvest_usgs


class FakeResponse:
    url = "https://waterservices.usgs.gov/nwis/iv/?format=json&sites=08211500"

    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self.payload


class FakeSession:
    def __init__(self, payload: dict) -> None:
        self.payload = payload
        self.calls: list[tuple] = []

    def get(self, url: str, params: dict, timeout: int) -> FakeResponse:
        self.calls.append((url, params, timeout))
        return FakeResponse(self.payload)


def test_harvest_writes_raw_normalized_and_metadata(tmp_path: Path) -> None:
    registry = tmp_path / "stations.yml"
    registry.write_text(
        """schema_version: 1
stations:
  - station_id: USGS-08211500
    agency: USGS
    agency_id: '08211500'
    name: Nueces River at Calallen, Texas
    waterbody: Nueces River
    role: primary
    status: active
    parameters: [discharge]
""",
        encoding="utf-8",
    )
    payload = json.loads(Path("tests/fixtures/usgs_iv_sample.json").read_text(encoding="utf-8"))
    result = harvest_usgs(
        registry,
        tmp_path / "data",
        date(2026, 7, 17),
        date(2026, 7, 17),
        session=FakeSession(payload),  # type: ignore[arg-type]
        now=datetime(2026, 7, 18, 1, 2, 3, tzinfo=UTC),
    )
    assert result.run_id == "20260718T010203Z"
    assert result.observation_count == 2
    assert result.raw_path.exists()
    assert result.normalized_path.exists()
    assert result.metadata_path.exists()
    with result.normalized_path.open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]["value"] == "25.0"
    metadata = json.loads(result.metadata_path.read_text(encoding="utf-8"))
    assert metadata["counts"] == {"observations": 2, "stations": 1}
    assert len(metadata["artifacts"]["raw_json"]["sha256"]) == 64
