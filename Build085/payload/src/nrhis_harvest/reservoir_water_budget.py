"""Reservoir-specific 24-hour water budgets for NRHIS daily operations."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import date, datetime, timezone
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class ReservoirWaterBudgetInput:
    day: date
    reservoir: str
    beginning_storage_acre_feet: float
    inflow_acre_feet: float
    municipal_diversions_acre_feet: float
    environmental_releases_acre_feet: float
    other_releases_acre_feet: float
    evaporation_low_acre_feet: float
    evaporation_high_acre_feet: float
    observed_ending_storage_acre_feet: float | None = None
    source: str = "NRHIS operational sources"
    confidence: str = "provisional"


def _validate(item: ReservoirWaterBudgetInput) -> None:
    nonnegative = (
        item.beginning_storage_acre_feet,
        item.inflow_acre_feet,
        item.municipal_diversions_acre_feet,
        item.environmental_releases_acre_feet,
        item.other_releases_acre_feet,
        item.evaporation_low_acre_feet,
        item.evaporation_high_acre_feet,
    )
    if any(value < 0 for value in nonnegative):
        raise ValueError("Water-budget inputs cannot be negative")
    if item.evaporation_low_acre_feet > item.evaporation_high_acre_feet:
        raise ValueError("Evaporation range is reversed")
    if item.observed_ending_storage_acre_feet is not None and item.observed_ending_storage_acre_feet < 0:
        raise ValueError("Observed ending storage cannot be negative")


def build_reservoir_water_budget(item: ReservoirWaterBudgetInput) -> dict[str, Any]:
    _validate(item)
    fixed_outflow = (
        item.municipal_diversions_acre_feet
        + item.environmental_releases_acre_feet
        + item.other_releases_acre_feet
    )
    net_change_low = item.inflow_acre_feet - fixed_outflow - item.evaporation_high_acre_feet
    net_change_high = item.inflow_acre_feet - fixed_outflow - item.evaporation_low_acre_feet
    projected_low = item.beginning_storage_acre_feet + net_change_low
    projected_high = item.beginning_storage_acre_feet + net_change_high

    residual_low = None
    residual_high = None
    if item.observed_ending_storage_acre_feet is not None:
        residual_low = item.observed_ending_storage_acre_feet - projected_high
        residual_high = item.observed_ending_storage_acre_feet - projected_low

    return {
        "input": asdict(item),
        "fixed_outflow_acre_feet": round(fixed_outflow, 2),
        "net_storage_change_low_acre_feet": round(net_change_low, 2),
        "net_storage_change_high_acre_feet": round(net_change_high, 2),
        "projected_ending_storage_low_acre_feet": round(projected_low, 2),
        "projected_ending_storage_high_acre_feet": round(projected_high, 2),
        "unaccounted_residual_low_acre_feet": None if residual_low is None else round(residual_low, 2),
        "unaccounted_residual_high_acre_feet": None if residual_high is None else round(residual_high, 2),
    }


def build_daily_reservoir_water_budgets(
    items: Iterable[ReservoirWaterBudgetInput],
    *,
    as_of: date,
) -> dict[str, Any]:
    budgets = [build_reservoir_water_budget(item) for item in items if item.day == as_of]
    names = [entry["input"]["reservoir"] for entry in budgets]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate reservoir budget for the same day")
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "as_of": as_of.isoformat(),
        "reservoirs": sorted(budgets, key=lambda entry: entry["input"]["reservoir"]),
        "caveat": (
            "Budgets are provisional and depend on the latest inflow, diversion, release, evaporation, "
            "and storage observations. Evaporation may use TexasET-derived proxy estimates when direct "
            "open-water measurements are unavailable."
        ),
    }


def render_water_budget_markdown(report: Mapping[str, Any]) -> str:
    lines = ["## 24-Hour Reservoir Water Budgets", ""]
    for budget in report.get("reservoirs", []):
        item = budget["input"]
        lines.extend(
            [
                f"### {item['reservoir']}",
                f"- Beginning storage: {item['beginning_storage_acre_feet']:,.2f} acre-feet",
                f"- Inflow: {item['inflow_acre_feet']:,.2f} acre-feet",
                f"- Municipal diversions: {item['municipal_diversions_acre_feet']:,.2f} acre-feet",
                f"- Environmental releases: {item['environmental_releases_acre_feet']:,.2f} acre-feet",
                f"- Other releases: {item['other_releases_acre_feet']:,.2f} acre-feet",
                f"- Evaporation: {item['evaporation_low_acre_feet']:,.2f}-{item['evaporation_high_acre_feet']:,.2f} acre-feet",
                f"- Net storage change: {budget['net_storage_change_low_acre_feet']:,.2f}-{budget['net_storage_change_high_acre_feet']:,.2f} acre-feet",
                f"- Projected ending storage: {budget['projected_ending_storage_low_acre_feet']:,.2f}-{budget['projected_ending_storage_high_acre_feet']:,.2f} acre-feet",
                f"- Confidence: {item['confidence']}",
                f"- Source: {item['source']}",
                "",
            ]
        )
    lines.extend(["**Operational caveat:** " + str(report.get("caveat", "")), ""])
    return "\n".join(lines)
