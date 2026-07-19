"""Data models used by the NRHIS harvest engine."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Station:
    """A configured monitoring station."""

    station_id: str
    agency: str
    agency_id: str
    name: str
    waterbody: str
    role: str
    status: str
    parameters: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class HarvestResult:
    """Paths and counts produced by a completed harvest."""

    run_id: str
    raw_path: Path
    normalized_path: Path
    metadata_path: Path
    station_count: int
    observation_count: int
