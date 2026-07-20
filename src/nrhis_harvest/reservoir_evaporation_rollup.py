"""Rolling reservoir evaporation totals and daily-operations integration for NRHIS."""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import date, datetime, timezone
from typing import Any, Iterable, Mapping


@dataclass(frozen=True)
class DailyEvaporationRecord:
    day: date
    reservoir: str
    low_acre_feet: float
    high_acre_feet: float
    low_million_gallons: float
    high_million_gallons: float
    method: str
    source: str
    confidence: str


def _validate(record: DailyEvaporationRecord) -> None:
    values = (
        record.low_acre_feet,
        record.high_acre_feet,
        record.low_million_gallons,
        record.high_million_gallons,
    )
    if any(value < 0 for value in values):
        raise ValueError("Evaporation losses cannot be negative")
    if record.low_acre_feet > record.high_acre_feet:
        raise ValueError("Acre-foot range is reversed")
    if record.low_million_gallons > record.high_million_gallons:
        raise ValueError("Million-gallon range is reversed")


def build_evaporation_rollup(
    records: Iterable[DailyEvaporationRecord],
    *,
    as_of: date,
    trailing_days: int = 7,
) -> dict[str, Any]:
    if trailing_days <= 0:
        raise ValueError("trailing_days must be positive")

    validated: list[DailyEvaporationRecord] = []
    for record in records:
        _validate(record)
        if record.day <= as_of:
            validated.append(record)

    by_reservoir: dict[str, list[DailyEvaporationRecord]] = {}
    for record in validated:
        by_reservoir.setdefault(record.reservoir, []).append(record)

    output: list[dict[str, Any]] = []
    for reservoir in sorted(by_reservoir):
        items = sorted(by_reservoir[reservoir], key=lambda item: item.day)
        trailing = items[-trailing_days:]
        month_items = [item for item in items if item.day.year == as_of.year and item.day.month == as_of.month]
        latest = items[-1]

        output.append(
            {
                "reservoir": reservoir,
                "as_of": as_of.isoformat(),
                "latest": asdict(latest),
                "trailing_day_count": len(trailing),
                "trailing_low_acre_feet": round(sum(x.low_acre_feet for x in trailing), 2),
                "trailing_high_acre_feet": round(sum(x.high_acre_feet for x in trailing), 2),
                "trailing_low_million_gallons": round(sum(x.low_million_gallons for x in trailing), 3),
                "trailing_high_million_gallons": round(sum(x.high_million_gallons for x in trailing), 3),
                "month_to_date_day_count": len(month_items),
                "month_to_date_low_acre_feet": round(sum(x.low_acre_feet for x in month_items), 2),
                "month_to_date_high_acre_feet": round(sum(x.high_acre_feet for x in month_items), 2),
                "month_to_date_low_million_gallons": round(sum(x.low_million_gallons for x in month_items), 3),
                "month_to_date_high_million_gallons": round(sum(x.high_million_gallons for x in month_items), 3),
            }
        )

    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "as_of": as_of.isoformat(),
        "trailing_days": trailing_days,
        "reservoirs": output,
        "caveat": (
            "Rolling totals preserve the source method for each day. TexasET-derived values remain estimates "
            "based on grass-reference ETo and configured open-water coefficients."
        ),
    }


def render_daily_operations_markdown(rollup: Mapping[str, Any]) -> str:
    lines = [
        "## Reservoir Evaporation Losses",
        "",
        "Daily, trailing-period, and month-to-date losses are shown separately for each reservoir.",
        "",
    ]
    for item in rollup.get("reservoirs", []):
        latest = item["latest"]
        lines.extend(
            [
                f"### {item['reservoir']}",
                f"- Daily loss ({latest['day']}): {latest['low_acre_feet']:,.2f}â€“{latest['high_acre_feet']:,.2f} acre-feet; "
                f"{latest['low_million_gallons']:,.3f}â€“{latest['high_million_gallons']:,.3f} million gallons",
                f"- Trailing {item['trailing_day_count']} days: {item['trailing_low_acre_feet']:,.2f}â€“{item['trailing_high_acre_feet']:,.2f} acre-feet; "
                f"{item['trailing_low_million_gallons']:,.3f}â€“{item['trailing_high_million_gallons']:,.3f} million gallons",
                f"- Month to date ({item['month_to_date_day_count']} days): {item['month_to_date_low_acre_feet']:,.2f}â€“{item['month_to_date_high_acre_feet']:,.2f} acre-feet; "
                f"{item['month_to_date_low_million_gallons']:,.3f}â€“{item['month_to_date_high_million_gallons']:,.3f} million gallons",
                f"- Method: {latest['method']}",
                f"- Source: {latest['source']}",
                f"- Confidence: {latest['confidence']}",
                "",
            ]
        )
    lines.extend(["**Method caveat:** " + str(rollup.get("caveat", "")), ""])
    return "\n".join(lines)
