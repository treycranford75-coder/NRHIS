from datetime import date

import pytest

from nrhis_harvest.reservoir_evaporation_rollup import (
    DailyEvaporationRecord,
    build_evaporation_rollup,
    render_daily_operations_markdown,
)


def rec(day: int, reservoir: str, low: float, high: float) -> DailyEvaporationRecord:
    return DailyEvaporationRecord(
        day=date(2026, 7, day),
        reservoir=reservoir,
        low_acre_feet=low,
        high_acre_feet=high,
        low_million_gallons=low * 0.325851429,
        high_million_gallons=high * 0.325851429,
        method="TexasET ETo proxy",
        source="Texas A&M AgriLife Extension TexasET Network",
        confidence="moderate",
    )


def test_builds_separate_reservoir_rollups() -> None:
    records = [rec(i, "Lake Corpus Christi", 10, 12) for i in range(1, 9)]
    records += [rec(i, "Choke Canyon Reservoir", 20, 25) for i in range(1, 9)]
    result = build_evaporation_rollup(records, as_of=date(2026, 7, 8), trailing_days=7)
    assert len(result["reservoirs"]) == 2
    lcc = next(x for x in result["reservoirs"] if x["reservoir"] == "Lake Corpus Christi")
    assert lcc["trailing_low_acre_feet"] == 70.0
    assert lcc["month_to_date_high_acre_feet"] == 96.0


def test_markdown_has_daily_trailing_and_mtd() -> None:
    result = build_evaporation_rollup([rec(8, "Lake Corpus Christi", 10, 12)], as_of=date(2026, 7, 8))
    text = render_daily_operations_markdown(result)
    assert "Daily loss" in text
    assert "Trailing 1 days" in text
    assert "Month to date" in text
    assert "million gallons" in text


def test_rejects_negative_values() -> None:
    bad = rec(8, "Lake Corpus Christi", -1, 2)
    with pytest.raises(ValueError):
        build_evaporation_rollup([bad], as_of=date(2026, 7, 8))
