from __future__ import annotations

import argparse
import json
from pathlib import Path

from nrhis_harvest.texaset_reservoir_evaporation import (
    build_reservoir_evaporation_summary,
    estimate_reservoir_evaporation,
    render_markdown,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", required=True)
    parser.add_argument("--regional-summary", required=True)
    parser.add_argument("--surface-areas", required=True)
    parser.add_argument("--output-json", required=True)
    parser.add_argument("--output-markdown", required=True)
    args = parser.parse_args()

    config = json.loads(Path(args.config).read_text(encoding="utf-8"))
    regional = json.loads(Path(args.regional_summary).read_text(encoding="utf-8"))
    surface_areas = json.loads(Path(args.surface_areas).read_text(encoding="utf-8"))

    regional_eto = {
        key: float(value["mean_daily_eto_in"])
        for key, value in regional.get("regions", {}).items()
    }
    estimates = []
    for key, item in config["reservoirs"].items():
        coefficient = item["open_water_coefficient"]
        estimates.append(
            estimate_reservoir_evaporation(
                reservoir=item["display_name"],
                surface_area_acres=float(surface_areas[key]["surface_area_acres"]),
                regional_eto_in=regional_eto,
                region_weights=item["regional_weights"],
                coefficient_low=float(coefficient["low"]),
                coefficient_high=float(coefficient["high"]),
                confidence=item.get("confidence", "moderate"),
            )
        )

    summary = build_reservoir_evaporation_summary(estimates)
    output_json = Path(args.output_json)
    output_markdown = Path(args.output_markdown)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_markdown.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    output_markdown.write_text(render_markdown(summary), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
