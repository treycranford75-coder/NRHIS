"""Load and validate NRHIS station registries."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from .models import Station

DEFAULT_PARAMETERS = ("discharge", "gage_height")
SUPPORTED_PARAMETERS = frozenset(DEFAULT_PARAMETERS)


class RegistryError(ValueError):
    """Raised when a station registry does not satisfy the NRHIS schema."""


def load_station_registry(path: Path) -> list[Station]:
    """Load active USGS stations from a YAML registry."""
    try:
        document: Any = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise RegistryError(f"Station registry not found: {path}") from exc
    except yaml.YAMLError as exc:
        raise RegistryError(f"Invalid YAML in station registry: {path}") from exc

    if not isinstance(document, dict) or document.get("schema_version") != 1:
        raise RegistryError("Station registry must be a mapping with schema_version: 1")
    entries = document.get("stations")
    if not isinstance(entries, list) or not entries:
        raise RegistryError("Station registry must contain a non-empty stations list")

    stations: list[Station] = []
    seen: set[str] = set()
    required = ("station_id", "agency", "agency_id", "name", "waterbody", "role", "status")
    for index, entry in enumerate(entries, start=1):
        if not isinstance(entry, dict):
            raise RegistryError(f"Station entry {index} must be a mapping")
        missing = [key for key in required if not entry.get(key)]
        if missing:
            raise RegistryError(f"Station entry {index} is missing: {', '.join(missing)}")
        station_id = str(entry["station_id"])
        if station_id in seen:
            raise RegistryError(f"Duplicate station_id: {station_id}")
        seen.add(station_id)

        parameters_raw = entry.get("parameters", DEFAULT_PARAMETERS)
        if not isinstance(parameters_raw, list | tuple) or not parameters_raw:
            raise RegistryError(f"Station {station_id} parameters must be a non-empty list")
        parameters = tuple(str(value) for value in parameters_raw)
        unsupported = sorted(set(parameters) - SUPPORTED_PARAMETERS)
        if unsupported:
            raise RegistryError(
                f"Station {station_id} has unsupported parameters: {', '.join(unsupported)}"
            )

        station = Station(
            station_id=station_id,
            agency=str(entry["agency"]).upper(),
            agency_id=str(entry["agency_id"]),
            name=str(entry["name"]),
            waterbody=str(entry["waterbody"]),
            role=str(entry["role"]),
            status=str(entry["status"]).lower(),
            parameters=parameters,
        )
        if station.agency == "USGS" and station.status == "active":
            stations.append(station)

    if not stations:
        raise RegistryError("Registry contains no active USGS stations")
    return stations
