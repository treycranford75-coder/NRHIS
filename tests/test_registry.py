from pathlib import Path

import pytest

from nrhis_harvest.registry import RegistryError, load_station_registry


def test_load_lower_nueces_registry_defaults_parameters() -> None:
    stations = load_station_registry(Path("config/stations/lower_nueces.yml"))
    assert len(stations) == 4
    assert stations[0].agency_id == "08210000"
    assert stations[0].parameters == ("discharge", "gage_height")


def test_registry_rejects_duplicate_station_ids(tmp_path: Path) -> None:
    path = tmp_path / "stations.yml"
    path.write_text(
        """schema_version: 1
stations:
  - &station
    station_id: USGS-1
    agency: USGS
    agency_id: '1'
    name: Test
    waterbody: River
    role: primary
    status: active
  - <<: *station
""",
        encoding="utf-8",
    )
    with pytest.raises(RegistryError, match="Duplicate station_id"):
        load_station_registry(path)
