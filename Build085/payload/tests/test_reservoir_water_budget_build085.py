from datetime import date

import pytest

from nrhis_harvest.reservoir_water_budget import (
    ReservoirWaterBudgetInput,
    build_daily_reservoir_water_budgets,
    build_reservoir_water_budget,
    render_water_budget_markdown,
)


def sample(name: str = "Lake Corpus Christi") -> ReservoirWaterBudgetInput:
    return ReservoirWaterBudgetInput(
        day=date(2026, 7, 20),
        reservoir=name,
        beginning_storage_acre_feet=100000.0,
        inflow_acre_feet=500.0,
        municipal_diversions_acre_feet=100.0,
        environmental_releases_acre_feet=25.0,
        other_releases_acre_feet=5.0,
        evaporation_low_acre_feet=20.0,
        evaporation_high_acre_feet=30.0,
        observed_ending_storage_acre_feet=100345.0,
    )


def test_budget_range_and_residual() -> None:
    result = build_reservoir_water_budget(sample())
    assert result["net_storage_change_low_acre_feet"] == 340.0
    assert result["net_storage_change_high_acre_feet"] == 350.0
    assert result["projected_ending_storage_low_acre_feet"] == 100340.0
    assert result["projected_ending_storage_high_acre_feet"] == 100350.0
    assert result["unaccounted_residual_low_acre_feet"] == -5.0
    assert result["unaccounted_residual_high_acre_feet"] == 5.0


def test_daily_report_has_two_separate_reservoirs() -> None:
    report = build_daily_reservoir_water_budgets(
        [sample("Lake Corpus Christi"), sample("Choke Canyon Reservoir")],
        as_of=date(2026, 7, 20),
    )
    assert len(report["reservoirs"]) == 2
    text = render_water_budget_markdown(report)
    assert "Lake Corpus Christi" in text
    assert "Choke Canyon Reservoir" in text
    assert "TexasET-derived proxy" in report["caveat"]


def test_negative_input_is_rejected() -> None:
    bad = ReservoirWaterBudgetInput(
        day=date(2026, 7, 20),
        reservoir="Lake Corpus Christi",
        beginning_storage_acre_feet=100.0,
        inflow_acre_feet=-1.0,
        municipal_diversions_acre_feet=0.0,
        environmental_releases_acre_feet=0.0,
        other_releases_acre_feet=0.0,
        evaporation_low_acre_feet=0.0,
        evaporation_high_acre_feet=0.0,
    )
    with pytest.raises(ValueError):
        build_reservoir_water_budget(bad)


def test_duplicate_reservoir_is_rejected() -> None:
    with pytest.raises(ValueError):
        build_daily_reservoir_water_budgets([sample(), sample()], as_of=date(2026, 7, 20))
