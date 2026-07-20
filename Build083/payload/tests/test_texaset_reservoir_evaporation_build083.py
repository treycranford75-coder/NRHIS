from __future__ import annotations

from datetime import datetime, timezone

import pytest

from nrhis_harvest.texaset_reservoir_evaporation import (
    build_reservoir_evaporation_summary,
    estimate_reservoir_evaporation,
    render_markdown,
)


def test_converts_eto_depth_to_af_and_mgd() -> None:
    result = estimate_reservoir_evaporation(
        reservoir="Lake Corpus Christi",
        surface_area_acres=10000,
        regional_eto_in={"coastal_bend": 0.20},
        region_weights={"coastal_bend": 1.0},
        coefficient_low=0.9,
        coefficient_high=1.1,
    )
    assert result.evaporation_low_acre_feet == 150.0
    assert result.evaporation_high_acre_feet == pytest.approx(183.33, abs=0.01)
    assert result.evaporation_low_mgd == pytest.approx(48.878, abs=0.001)
    assert result.status == "estimated_from_reference_eto"


def test_supports_weighted_regional_eto() -> None:
    result = estimate_reservoir_evaporation(
        reservoir="Choke Canyon Reservoir",
        surface_area_acres=5000,
        regional_eto_in={"coastal_bend": 0.18, "winter_garden": 0.22},
        region_weights={"coastal_bend": 0.5, "winter_garden": 0.5},
        coefficient_low=1.0,
        coefficient_high=1.0,
    )
    assert result.reference_eto_in == 0.20
    assert result.source_regions == ("coastal_bend", "winter_garden")


def test_rejects_missing_region_and_invalid_inputs() -> None:
    with pytest.raises(KeyError):
        estimate_reservoir_evaporation(
            reservoir="Test",
            surface_area_acres=100,
            regional_eto_in={"coastal_bend": 0.1},
            region_weights={"winter_garden": 1.0},
            coefficient_low=0.8,
            coefficient_high=1.2,
        )
    with pytest.raises(ValueError):
        estimate_reservoir_evaporation(
            reservoir="Test",
            surface_area_acres=0,
            regional_eto_in={"coastal_bend": 0.1},
            region_weights={"coastal_bend": 1.0},
            coefficient_low=0.8,
            coefficient_high=1.2,
        )


def test_summary_and_markdown_preserve_estimate_caveat() -> None:
    estimate = estimate_reservoir_evaporation(
        reservoir="Lake Corpus Christi",
        surface_area_acres=1000,
        regional_eto_in={"coastal_bend": 0.12},
        region_weights={"coastal_bend": 1.0},
        coefficient_low=0.9,
        coefficient_high=1.1,
    )
    summary = build_reservoir_evaporation_summary(
        [estimate], generated_at=datetime(2026, 7, 20, tzinfo=timezone.utc)
    )
    text = render_markdown(summary)
    assert summary["classification"] == "estimated open-water evaporation range"
    assert "not a direct open-water measurement" in text
    assert "MGD" in text
