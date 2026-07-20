from __future__ import annotations

from datetime import date

import pytest

from nrhis_harvest.reservoir_water_budget import (
    _daily_evap,
    build_budget,
    evaporation_acft,
)


def _config() -> dict:
    return {
        "monthly_climatology_inches_per_day": {
            "7": 0.18,
        },
        "reservoirs": {
            "choke-canyon": {
                "display_name": "Choke Canyon Reservoir",
            },
            "lake-corpus-christi": {
                "display_name": "Lake Corpus Christi",
            },
        },
    }


def test_evaporation_acft_calculation() -> None:
    assert evaporation_acft(10_000.0, 0.24) == pytest.approx(200.0)


@pytest.mark.parametrize(
    ("surface_area", "inches"),
    [
        (None, 0.24),
        (10_000.0, None),
        (None, None),
    ],
)
def test_evaporation_acft_missing_input(
    surface_area: float | None,
    inches: float | None,
) -> None:
    assert evaporation_acft(surface_area, inches) is None


def test_daily_evap_matches_reservoir_and_date() -> None:
    data = [
        {
            "reservoir_id": "choke-canyon",
            "date": "2026-07-19",
            "evaporation_inches": 0.21,
            "source": "verified daily evaporation",
        },
        {
            "reservoir_id": "lake-corpus-christi",
            "date": "2026-07-19",
            "evaporation_inches": 0.17,
            "source": "other reservoir",
        },
    ]

    value, source, method = _daily_evap(
        data,
        "choke-canyon",
        "2026-07-19",
    )

    assert value == pytest.approx(0.21)
    assert source == "verified daily evaporation"
    assert method == "daily observed/estimated evaporation"


def test_daily_evap_returns_missing_when_no_match() -> None:
    value, source, method = _daily_evap(
        [],
        "choke-canyon",
        "2026-07-19",
    )

    assert value is None
    assert source == ""
    assert method == ""


def test_build_budget_uses_daily_evaporation_and_complete_fluxes() -> None:
    reservoirs = [
        {
            "reservoir_id": "choke-canyon",
            "reservoir_name": "Choke Canyon Reservoir",
            "surface_area_acres": 10_000.0,
            "storage_change_acft": 345.0,
        }
    ]
    evaporation_data = [
        {
            "reservoir_id": "choke-canyon",
            "date": "2026-07-19",
            "evaporation_inches": 0.24,
            "source": "daily dataset",
        }
    ]
    flux_data = [
        {
            "reservoir_id": "choke-canyon",
            "inflow_acft": 500.0,
            "municipal_diversions_acft": 100.0,
            "environmental_releases_acft": 25.0,
            "other_outflow_acft": 10.0,
        }
    ]

    rows = build_budget(
        reservoirs,
        _config(),
        report_date=date(2026, 7, 19),
        evaporation_data=evaporation_data,
        flux_data=flux_data,
        history_rows=[],
    )

    assert len(rows) == 1
    row = rows[0]

    assert row.reservoir_id == "choke-canyon"
    assert row.evaporation_inches_per_day == pytest.approx(0.24)
    assert row.evaporation_source == "daily dataset"
    assert row.evaporation_acft_per_day == pytest.approx(200.0)
    assert row.budget_complete is True
    assert row.calculated_net_change_acft == pytest.approx(165.0)
    assert row.budget_residual_acft == pytest.approx(180.0)


def test_build_budget_uses_monthly_climatology_fallback() -> None:
    reservoirs = [
        {
            "reservoir_id": "lake-corpus-christi",
            "reservoir_name": "Lake Corpus Christi",
            "surface_area_acres": 5_000.0,
            "storage_change_acft": None,
        }
    ]

    rows = build_budget(
        reservoirs,
        _config(),
        report_date=date(2026, 7, 19),
        evaporation_data=None,
        flux_data=None,
        history_rows=[],
    )

    row = rows[0]

    assert row.evaporation_inches_per_day == pytest.approx(0.18)
    assert row.evaporation_source == "configured monthly climatology fallback"
    assert "monthly climatology" in row.evaporation_method
    assert "estimate" in row.evaporation_method
    assert row.evaporation_acft_per_day == pytest.approx(75.0)
    assert row.budget_complete is False
    assert row.calculated_net_change_acft is None
    assert row.budget_residual_acft is None


def test_build_budget_calculates_rolling_evaporation_totals() -> None:
    history = [
        {
            "reservoir_id": "choke-canyon",
            "report_date": f"2026-07-{day:02d}",
            "evaporation_acft_per_day": 10.0,
        }
        for day in range(13, 19)
    ]

    rows = build_budget(
        [
            {
                "reservoir_id": "choke-canyon",
                "reservoir_name": "Choke Canyon Reservoir",
                "surface_area_acres": 1_000.0,
                "storage_change_acft": None,
            }
        ],
        _config(),
        report_date=date(2026, 7, 19),
        evaporation_data=[
            {
                "reservoir_id": "choke-canyon",
                "date": "2026-07-19",
                "evaporation_inches": 0.12,
                "source": "daily dataset",
            }
        ],
        flux_data=None,
        history_rows=history,
    )

    row = rows[0]

    assert row.evaporation_acft_per_day == pytest.approx(10.0)
    assert row.evaporation_7day_acft == pytest.approx(70.0)
    assert row.evaporation_month_to_date_acft == pytest.approx(70.0)


def test_build_budget_handles_missing_surface_area() -> None:
    rows = build_budget(
        [
            {
                "reservoir_id": "choke-canyon",
                "reservoir_name": "Choke Canyon Reservoir",
                "surface_area_acres": None,
                "storage_change_acft": 0.0,
            }
        ],
        _config(),
        report_date=date(2026, 7, 19),
        evaporation_data=None,
        flux_data=[],
        history_rows=[],
    )

    row = rows[0]

    assert row.evaporation_acft_per_day is None
    assert row.evaporation_mgd is None
    assert row.budget_complete is False
