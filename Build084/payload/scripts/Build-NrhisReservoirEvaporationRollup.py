from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from nrhis_harvest.reservoir_evaporation_rollup import (
    DailyEvaporationRecord,
    build_evaporation_rollup,
    render_daily_operations_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--json-output", required=True)
    parser.add_argument("--markdown-output", required=True)
    parser.add_argument("--trailing-days", type=int, default=7)
    args = parser.parse_args()

    raw = json.loads(Path(args.input).read_text(encoding="utf-8"))
    records = [
        DailyEvaporationRecord(
            day=date.fromisoformat(item["day"]),
            reservoir=item["reservoir"],
            low_acre_feet=float(item["low_acre_feet"]),
            high_acre_feet=float(item["high_acre_feet"]),
            low_million_gallons=float(item["low_million_gallons"]),
            high_million_gallons=float(item["high_million_gallons"]),
            method=item["method"],
            source=item["source"],
            confidence=item["confidence"],
        )
        for item in raw["records"]
    ]
    rollup = build_evaporation_rollup(
        records,
        as_of=date.fromisoformat(args.as_of),
        trailing_days=args.trailing_days,
    )

    json_path = Path(args.json_output)
    markdown_path = Path(args.markdown_output)
    json_path.parent.mkdir(parents=True, exist_ok=True)
    markdown_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(rollup, indent=2, default=str) + "\n", encoding="utf-8")
    markdown_path.write_text(render_daily_operations_markdown(rollup), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
