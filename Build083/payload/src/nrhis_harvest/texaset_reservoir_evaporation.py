"""TexasET-informed reservoir evaporation estimates for NRHIS.

TexasET reports grass-reference evapotranspiration (ETo), not direct open-water
reservoir evaporation. This module applies an explicitly configured coefficient
range to verified regional ETo and converts the resulting depth to reservoir
volume. Outputs remain estimates and preserve the source/proxy distinction.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Any, Mapping, Sequence

ACRE_FEET_TO_MILLION_GALLONS = 0.325851429


@dataclass(frozen=True)
class ReservoirEstimate:
    reservoir: str
    surface_area_acres: float
    reference_eto_in: float
    coefficient_low: float
    coefficient_high: float
    evaporation_depth_low_in: float
    evaporation_depth_high_in: float
    evaporation_low_acre_feet: float
    evaporation_high_acre_feet: float
    evaporation_low_mgd: float
    evaporation_high_mgd: float
    confidence: str
    status: str
    source_regions: tuple[str, ...]


def _weighted_eto(
    regional_eto: Mapping[str, float],
    weights: Mapping[str, float],
) -> tuple[float, tuple[str, ...]]:
    if not weights:
        raise ValueError("At least one TexasET regional weight is required")
    total_weight = 0.0
    weighted_sum = 0.0
    used: list[str] = []
    for region, raw_weight in weights.items():
        weight = float(raw_weight)
        if weight < 0:
            raise ValueError("TexasET regional weights cannot be negative")
        if weight == 0:
            continue
        if region not in regional_eto:
            raise KeyError(f"Missing TexasET regional ETo: {region}")
        eto = float(regional_eto[region])
        if eto < 0:
            raise ValueError("TexasET ETo cannot be negative")
        weighted_sum += eto * weight
        total_weight += weight
        used.append(region)
    if total_weight <= 0:
        raise ValueError("TexasET regional weights must total more than zero")
    return weighted_sum / total_weight, tuple(sorted(used))


def estimate_reservoir_evaporation(
    *,
    reservoir: str,
    surface_area_acres: float,
    regional_eto_in: Mapping[str, float],
    region_weights: Mapping[str, float],
    coefficient_low: float,
    coefficient_high: float,
    confidence: str = "moderate",
) -> ReservoirEstimate:
    area = float(surface_area_acres)
    low = float(coefficient_low)
    high = float(coefficient_high)
    if area <= 0:
        raise ValueError("Reservoir surface area must be positive")
    if low <= 0 or high <= 0 or low > high:
        raise ValueError("Evaporation coefficients must be positive and ordered")

    eto, regions = _weighted_eto(regional_eto_in, region_weights)
    depth_low = eto * low
    depth_high = eto * high
    af_low = area * depth_low / 12.0
    af_high = area * depth_high / 12.0

    return ReservoirEstimate(
        reservoir=reservoir,
        surface_area_acres=round(area, 2),
        reference_eto_in=round(eto, 4),
        coefficient_low=low,
        coefficient_high=high,
        evaporation_depth_low_in=round(depth_low, 4),
        evaporation_depth_high_in=round(depth_high, 4),
        evaporation_low_acre_feet=round(af_low, 2),
        evaporation_high_acre_feet=round(af_high, 2),
        evaporation_low_mgd=round(af_low * ACRE_FEET_TO_MILLION_GALLONS, 3),
        evaporation_high_mgd=round(af_high * ACRE_FEET_TO_MILLION_GALLONS, 3),
        confidence=confidence,
        status="estimated_from_reference_eto",
        source_regions=regions,
    )


def build_reservoir_evaporation_summary(
    estimates: Sequence[ReservoirEstimate],
    *,
    generated_at: datetime | None = None,
) -> dict[str, Any]:
    now = generated_at or datetime.now(timezone.utc)
    return {
        "schema_version": 1,
        "generated_at": now.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": "Texas A&M AgriLife Extension TexasET Network",
        "source_variable": "grass-reference evapotranspiration (ETo)",
        "classification": "estimated open-water evaporation range",
        "reservoirs": [asdict(item) for item in estimates],
        "caveat": (
            "TexasET ETo is not a direct measurement of reservoir evaporation. "
            "Ranges use configured open-water coefficients and current surface area; "
            "replace with verified pan, energy-budget, or reservoir-specific evaporation data when available."
        ),
    }


def render_markdown(summary: Mapping[str, Any]) -> str:
    lines = [
        "## TexasET-Informed Reservoir Evaporation",
        "",
        "**Status:** Estimated from grass-reference ETo; not a direct open-water measurement.",
        "",
    ]
    for item in summary.get("reservoirs", []):
        regions = ", ".join(item.get("source_regions", [])) or "not available"
        lines.extend(
            [
                f"### {item['reservoir']}",
                f"- Surface area: {item['surface_area_acres']:,.2f} acres",
                f"- Reference ETo: {item['reference_eto_in']:.4f} in/day",
                f"- Estimated evaporation depth: {item['evaporation_depth_low_in']:.4f}–{item['evaporation_depth_high_in']:.4f} in/day",
                f"- Estimated loss: {item['evaporation_low_acre_feet']:,.2f}–{item['evaporation_high_acre_feet']:,.2f} acre-feet/day",
                f"- Estimated loss: {item['evaporation_low_mgd']:,.3f}–{item['evaporation_high_mgd']:,.3f} MGD",
                f"- TexasET regions used: {regions}",
                f"- Confidence: {item['confidence']}",
                "",
            ]
        )
    lines.extend(["**Method caveat:** " + str(summary.get("caveat", "")), ""])
    return "\n".join(lines)
