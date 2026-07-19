"""USGS NWIS Instantaneous Values client and response normalization."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date
from typing import Any

import requests

from .models import Station

NWIS_IV_URL = "https://waterservices.usgs.gov/nwis/iv/"
PARAMETER_CODES = {"discharge": "00060", "gage_height": "00065"}
PARAMETER_NAMES = {"00060": "discharge", "00065": "gage_height"}


class UsgsError(RuntimeError):
    """Raised when the USGS request or response is invalid."""


def build_query(stations: Iterable[Station], start: date, end: date) -> dict[str, str]:
    """Build a deterministic USGS IV request query."""
    station_list = list(stations)
    parameter_names = sorted({name for station in station_list for name in station.parameters})
    return {
        "format": "json",
        "sites": ",".join(station.agency_id for station in station_list),
        "parameterCd": ",".join(PARAMETER_CODES[name] for name in parameter_names),
        "startDT": start.isoformat(),
        "endDT": end.isoformat(),
        "siteStatus": "all",
    }


def download(
    session: requests.Session,
    query: dict[str, str],
    timeout_seconds: int = 60,
) -> tuple[dict[str, Any], str]:
    """Download and decode one USGS NWIS JSON response."""
    try:
        response = session.get(NWIS_IV_URL, params=query, timeout=timeout_seconds)
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException as exc:
        raise UsgsError(f"USGS NWIS request failed: {exc}") from exc
    except ValueError as exc:
        raise UsgsError("USGS NWIS returned invalid JSON") from exc
    if not isinstance(payload, dict) or "value" not in payload:
        raise UsgsError("USGS NWIS response is missing the value object")
    return payload, response.url


def normalize(payload: dict[str, Any], stations: Iterable[Station]) -> list[dict[str, Any]]:
    """Normalize NWIS WaterML JSON time series into stable observation records."""
    station_lookup = {station.agency_id: station for station in stations}
    records: list[dict[str, Any]] = []
    time_series = payload.get("value", {}).get("timeSeries", [])
    if not isinstance(time_series, list):
        raise UsgsError("USGS NWIS response has an invalid timeSeries collection")

    for series in time_series:
        source_info = series.get("sourceInfo", {})
        site_codes = source_info.get("siteCode", [])
        agency_id = str(site_codes[0].get("value", "")) if site_codes else ""
        station = station_lookup.get(agency_id)
        if station is None:
            continue
        variable = series.get("variable", {})
        variable_codes = variable.get("variableCode", [])
        parameter_code = str(variable_codes[0].get("value", "")) if variable_codes else ""
        parameter = PARAMETER_NAMES.get(parameter_code, parameter_code or "unknown")
        unit = str(variable.get("unit", {}).get("unitCode", ""))
        value_groups = series.get("values", [])
        for value_group in value_groups:
            for observation in value_group.get("value", []):
                raw_value = observation.get("value")
                try:
                    numeric_value = float(raw_value)
                except (TypeError, ValueError):
                    numeric_value = None
                qualifiers = observation.get("qualifiers", [])
                records.append(
                    {
                        "station_id": station.station_id,
                        "agency": station.agency,
                        "agency_id": station.agency_id,
                        "station_name": station.name,
                        "waterbody": station.waterbody,
                        "role": station.role,
                        "parameter": parameter,
                        "parameter_code": parameter_code,
                        "unit": unit,
                        "observed_at": observation.get("dateTime", ""),
                        "value": numeric_value,
                        "qualifiers": "|".join(str(item) for item in qualifiers),
                        "source": "USGS NWIS IV",
                    }
                )
    records.sort(key=lambda item: (item["station_id"], item["parameter_code"], item["observed_at"]))
    return records
