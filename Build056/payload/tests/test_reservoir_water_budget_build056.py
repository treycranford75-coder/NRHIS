from datetime import date
from nrhis_harvest.reservoir_water_budget import build_budget, evaporation_acft


def test_evaporation_conversion():
    assert evaporation_acft(12000, 0.24) == 240.0


def test_budget_with_fallback_and_fluxes():
    reservoirs = [
        {
            "reservoir_id": "ChokeCanyon",
            "reservoir_name": "Choke Canyon Reservoir",
            "surface_area_acres": 10000,
            "storage_change_acft": 100,
        }
    ]
    config = {
        "monthly_climatology_inches_per_day": {"7": 0.30},
        "reservoirs": {"ChokeCanyon": {"display_name": "Choke Canyon Reservoir"}},
    }
    rows = build_budget(
        reservoirs,
        config,
        report_date=date(2026, 7, 19),
        flux_data=[
            {
                "reservoir_id": "ChokeCanyon",
                "inflow_acft": 500,
                "municipal_diversions_acft": 100,
                "environmental_releases_acft": 50,
                "other_outflow_acft": 0,
            }
        ],
    )
    row = rows[0]
    assert row.evaporation_acft_per_day == 250.0
    assert row.calculated_net_change_acft == 100.0
    assert row.budget_residual_acft == 0.0
    assert row.budget_complete
    assert "climatology" in row.evaporation_source
