#!/usr/bin/env python3
"""Build NRHIS daily reservoir water-budget JSON and Markdown outputs."""
from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from nrhis_harvest.reservoir_water_budget import (
    ReservoirWaterBudgetInput,
    build_daily_reservoir_water_budgets,
    render_water_budget_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--json-output", required=True, type=Path)
    parser.add_argument("--markdown-output", required=True, type=Path)
    args = parser.parse_args()

    raw = json.loads(args.input.read_text(encoding="utf-8"))
    items = [ReservoirWaterBudgetInput(day=date.fromisoformat(row["day"]), **{k: v for k, v in row.items() if k != "day"}) for row in raw["reservoirs"]]
    report = build_daily_reservoir_water_budgets(items, as_of=date.fromisoformat(args.as_of))
    args.json_output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.json_output.write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    args.markdown_output.write_text(render_water_budget_markdown(report), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
