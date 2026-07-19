from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from nrhis_harvest import twdb_reservoir_harvest as twdb


def _config() -> dict:
    return {
        "api_url": "https://example.test/reservoirs.geojson",
        "timeout_seconds": 30,
        "stale_days": 3,
        "reservoirs": [
            {
                "condensed_name": "choke-canyon",
                "display_name": "Choke Canyon Reservoir",
                "display_order": 1,
            },
            {
                "condensed_name": "lake-corpus-christi",
                "display_name": "Lake Corpus Christi",
                "display_order": 2,
            },
        ],
    }


def _payload() -> dict:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "condensed_name": "lake-corpus-christi",
                    "full_name": "Lake Corpus Christi",
                    "timestamp": "2026-07-18",
                    "elevation": "93.10",
                    "conservation_storage": "150000",
                    "conservation_capacity": "256062",
                    "percent_full": "58.6",
                    "area": "12100",
                    "volume": "150000",
                },
            },
            {
                "type": "Feature",
                "properties": {
                    "condensed_name": "choke-canyon",
                    "full_name": "",
                    "timestamp": "2026-07-19",
                    "elevation": 195.4,
                    "conservation_storage": 220000,
                    "conservation_capacity": 695271,
                    "percent_full": 31.6,
                    "area": 14500,
                    "volume": 220000,
                },
            },
        ],
    }


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, None),
        ("", None),
        ("null", None),
        ("12.5", 12.5),
        (7, 7.0),
        ("not-a-number", None),
        ({}, None),
    ],
)
def test_number_normalization(value: object, expected: float | None) -> None:
    assert twdb._number(value) == expected


def test_atomic_write_and_csv_write(tmp_path: Path) -> None:
    text_path = tmp_path / "nested" / "output.json"
    twdb._atomic_write(text_path, '{"ok": true}\n')

    assert text_path.read_text(encoding="utf-8") == '{"ok": true}\n'

    csv_path = tmp_path / "nested" / "output.csv"
    twdb._write_csv(
        csv_path,
        [
            {"reservoir_id": "choke-canyon", "storage": 220000},
            {"reservoir_id": "lake-corpus-christi", "storage": 150000},
        ],
    )

    csv_text = csv_path.read_text(encoding="utf-8")
    assert "reservoir_id,storage" in csv_text
    assert "choke-canyon,220000" in csv_text


def test_write_empty_csv_uses_reservoir_id_header(tmp_path: Path) -> None:
    csv_path = tmp_path / "empty.csv"
    twdb._write_csv(csv_path, [])

    assert csv_path.read_text(encoding="utf-8").strip() == "reservoir_id"


def test_prior_storage_missing_invalid_and_valid(tmp_path: Path) -> None:
    missing = tmp_path / "missing.json"
    assert twdb._prior_storage(missing) == {}

    invalid = tmp_path / "invalid.json"
    invalid.write_text("{broken", encoding="utf-8")
    assert twdb._prior_storage(invalid) == {}

    valid = tmp_path / "valid.json"
    valid.write_text(
        json.dumps(
            [
                {
                    "reservoir_id": "choke-canyon",
                    "conservation_storage_acft": "200000",
                },
                {
                    "reservoir_id": "",
                    "conservation_storage_acft": 10,
                },
                {
                    "reservoir_id": "bad-value",
                    "conservation_storage_acft": "invalid",
                },
                "not-a-dictionary",
            ]
        ),
        encoding="utf-8",
    )

    assert twdb._prior_storage(valid) == {"choke-canyon": 200000.0}


def test_parse_geojson_normalizes_orders_and_storage_changes() -> None:
    observations = twdb.parse_geojson(
        _payload(),
        _config(),
        now=datetime(2026, 7, 20, tzinfo=timezone.utc),
        prior_storage={
            "choke-canyon": 210000.0,
            "lake-corpus-christi": 149500.0,
        },
    )

    assert [row.reservoir_id for row in observations] == [
        "choke-canyon",
        "lake-corpus-christi",
    ]

    choke = observations[0]
    lake = observations[1]

    assert choke.reservoir_name == "Choke Canyon Reservoir"
    assert choke.storage_change_acft == pytest.approx(10000.0)
    assert choke.stale is False
    assert choke.identity == "choke-canyon|2026-07-19"

    assert lake.storage_change_acft == pytest.approx(500.0)
    assert lake.stale is False
    assert lake.surface_area_acres == pytest.approx(12100.0)


def test_parse_geojson_skips_irrelevant_features() -> None:
    payload = _payload()
    payload["features"].insert(0, "not-a-feature")
    payload["features"].insert(
        1,
        {
            "type": "Feature",
            "properties": {
                "condensed_name": "unconfigured-reservoir",
                "timestamp": "2026-07-19",
            },
        },
    )

    observations = twdb.parse_geojson(
        payload,
        _config(),
        now=datetime(2026, 7, 20, tzinfo=timezone.utc),
    )

    assert len(observations) == 2


def test_parse_geojson_rejects_missing_features() -> None:
    with pytest.raises(
        twdb.ReservoirHarvestError,
        match="missing a GeoJSON features list",
    ):
        twdb.parse_geojson(
            {},
            _config(),
            now=datetime(2026, 7, 20, tzinfo=timezone.utc),
        )


def test_parse_geojson_rejects_empty_configuration() -> None:
    with pytest.raises(
        twdb.ReservoirHarvestError,
        match="contains no reservoirs",
    ):
        twdb.parse_geojson(
            {"features": []},
            {"reservoirs": []},
            now=datetime(2026, 7, 20, tzinfo=timezone.utc),
        )


def test_parse_geojson_rejects_invalid_timestamp() -> None:
    payload = _payload()
    payload["features"][0]["properties"]["timestamp"] = "not-a-date"

    with pytest.raises(
        twdb.ReservoirHarvestError,
        match="Invalid reservoir timestamp",
    ):
        twdb.parse_geojson(
            payload,
            _config(),
            now=datetime(2026, 7, 20, tzinfo=timezone.utc),
        )


def test_parse_geojson_rejects_missing_configured_reservoir() -> None:
    payload = _payload()
    payload["features"] = payload["features"][:1]

    with pytest.raises(
        twdb.ReservoirHarvestError,
        match="Configured reservoirs missing",
    ):
        twdb.parse_geojson(
            payload,
            _config(),
            now=datetime(2026, 7, 20, tzinfo=timezone.utc),
        )


def test_parse_geojson_marks_old_observation_stale() -> None:
    payload = _payload()
    payload["features"][0]["properties"]["timestamp"] = "2026-07-01"

    observations = twdb.parse_geojson(
        payload,
        _config(),
        now=datetime(2026, 7, 20, tzinfo=timezone.utc),
    )

    lake = next(row for row in observations if row.reservoir_id == "lake-corpus-christi")
    assert lake.stale is True


def test_append_deduplicated_jsonl(tmp_path: Path) -> None:
    path = tmp_path / "history.jsonl"

    observations = twdb.parse_geojson(
        _payload(),
        _config(),
        now=datetime(2026, 7, 20, tzinfo=timezone.utc),
    )

    assert twdb.append_deduplicated_jsonl(path, observations) == 2
    assert twdb.append_deduplicated_jsonl(path, observations) == 0
    assert len(path.read_text(encoding="utf-8").splitlines()) == 2


class _FakeResponse:
    def __init__(self, payload: bytes, status: int = 200) -> None:
        self.payload = payload
        self.status = status

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *args: object) -> None:
        return None

    def read(self) -> bytes:
        return self.payload


def test_fetch_bytes_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        twdb.urllib.request,
        "urlopen",
        lambda request, timeout: _FakeResponse(b'{"ok":true}', 200),
    )

    assert twdb.fetch_bytes("https://example.test", 10) == b'{"ok":true}'


def test_fetch_bytes_rejects_non_200(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        twdb.urllib.request,
        "urlopen",
        lambda request, timeout: _FakeResponse(b"error", 503),
    )

    with pytest.raises(
        twdb.ReservoirHarvestError,
        match="HTTP 503",
    ):
        twdb.fetch_bytes("https://example.test", 10)


def test_harvest_writes_outputs_and_receipt(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(_config()), encoding="utf-8")

    fixed_time = datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc)

    monkeypatch.setattr(twdb, "utc_now", lambda: fixed_time)
    monkeypatch.setattr(
        twdb,
        "fetch_bytes",
        lambda url, timeout_seconds=60: json.dumps(_payload()).encode("utf-8"),
    )

    receipt = twdb.harvest(config_path, tmp_path / "data")

    assert receipt["reservoir_count"] == 2
    assert receipt["new_history_records"] == 2
    assert receipt["stale_reservoirs"] == []
    assert len(receipt["raw_sha256"]) == 64

    current_json = Path(receipt["files"]["current_json"])
    current_csv = Path(receipt["files"]["current_csv"])
    combined_path = Path(receipt["files"]["combined_summary"])
    history_path = Path(receipt["files"]["history_jsonl"])
    receipt_path = Path(receipt["receipt_path"])

    assert current_json.exists()
    assert current_csv.exists()
    assert combined_path.exists()
    assert history_path.exists()
    assert receipt_path.exists()

    combined = json.loads(combined_path.read_text(encoding="utf-8"))
    assert combined["reservoir_count"] == 2
    assert combined["combined_conservation_storage_acft"] == pytest.approx(370000.0)
    assert combined["combined_conservation_capacity_acft"] == pytest.approx(951333.0)
    assert combined["combined_percent_full"] == pytest.approx(38.9)

    second_receipt = twdb.harvest(config_path, tmp_path / "data")
    assert second_receipt["new_history_records"] == 0
