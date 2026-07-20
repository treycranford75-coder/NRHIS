"""TexasET regional evapotranspiration ingestion for NRHIS.

The parser is deliberately transport-agnostic: callers can provide normalized
station records from a website adapter, cached export, or manually verified
TexasET download. This keeps the operational report deterministic while the
site adapter evolves.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from statistics import mean
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class TexasETObservation:
    station: str
    region: str
    observed_at: str
    eto_in: float
    rainfall_in: float
    source_url: str
    status: str = "observed"

    @classmethod
    def from_mapping(cls, item: Mapping[str, Any]) -> "TexasETObservation":
        eto = float(item["eto_in"])
        rain = float(item.get("rainfall_in", 0.0))
        if eto < 0:
            raise ValueError("TexasET ETo cannot be negative")
        if rain < 0:
            raise ValueError("TexasET rainfall cannot be negative")
        observed = str(item["observed_at"])
        datetime.fromisoformat(observed.replace("Z", "+00:00"))
        return cls(
            station=str(item["station"]).strip(),
            region=str(item["region"]).strip(),
            observed_at=observed,
            eto_in=eto,
            rainfall_in=rain,
            source_url=str(item["source_url"]).strip(),
            status=str(item.get("status", "observed")),
        )


def build_regional_summary(
    observations: Iterable[TexasETObservation],
    *,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    rows = list(observations)
    now = generated_at or datetime.now(timezone.utc)
    grouped: dict[str, list[TexasETObservation]] = {}
    for row in rows:
        grouped.setdefault(row.region, []).append(row)

    regions: dict[str, Any] = {}
    for region, items in sorted(grouped.items()):
        regions[region] = {
            "station_count": len(items),
            "mean_daily_eto_in": round(mean(x.eto_in for x in items), 3),
            "total_daily_rainfall_in": round(sum(x.rainfall_in for x in items), 3),
            "stations": [asdict(x) for x in sorted(items, key=lambda x: x.station)],
        }

    return {
        "schema_version": 1,
        "generated_at": now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": "Texas A&M AgriLife Extension TexasET Network",
        "method": "ASCE standardized Penman-Monteith reference ET",
        "regions": regions,
    }


def render_markdown(summary: Mapping[str, Any]) -> str:
    lines = [
        "## TexasET Regional Evapotranspiration",
        "",
        "Source: Texas A&M AgriLife Extension TexasET Network.",
        "ETo is grass-reference evapotranspiration and is not direct reservoir evaporation.",
        "",
    ]
    for key, region in summary.get("regions", {}).items():
        title = key.replace("_", " ").title()
        lines.extend([
            f"### {title}",
            f"- Reporting stations: {region['station_count']}",
            f"- Mean daily ETo: {region['mean_daily_eto_in']:.3f} in",
            f"- Station rainfall total: {region['total_daily_rainfall_in']:.3f} in",
            "",
        ])
    if not summary.get("regions"):
        lines.extend(["No verified TexasET station observations were available for this cycle.", ""])
    return "\n".join(lines)
