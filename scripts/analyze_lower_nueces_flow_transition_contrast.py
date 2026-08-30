from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_src = Path(__file__).resolve().parents[1] / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from nrhis_analysis.lower_nueces_flow_transition_contrast import (  # noqa: E402
    analyze_lower_nueces_flow_transition_contrast,
)
from nrhis_analysis.usgs_history_query import QueryError  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Analyze lower Nueces upper-flow transition contrast using disjoint "
            "lower/upper subsets and non-overlapping flow bands."
        )
    )
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--index", required=True, type=Path)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--min-observations-per-hour", type=int, default=2)
    parser.add_argument("--max-lag-hours", type=int, default=72)
    parser.add_argument("--min-paired-hours", type=int, default=48)
    parser.add_argument("--percentile-step", type=int, default=5)
    parser.add_argument("--min-transition-percentile", type=int, default=60)
    parser.add_argument("--max-transition-percentile", type=int, default=90)
    parser.add_argument("--coherence-r", type=float, default=0.8)
    parser.add_argument("--strong-r", type=float, default=0.9)
    parser.add_argument("--max-lower-r", type=float, default=0.5)
    parser.add_argument("--confirm-steps", type=int, default=2)
    parser.add_argument("--band-width-percentile", type=int, default=20)
    parser.add_argument("--event-gap-tolerance-hours", type=int, default=2)
    parser.add_argument("--min-event-high-hours", type=int, default=12)
    parser.add_argument("--event-min-paired-hours", type=int, default=6)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = args.output_root.resolve() / f"lower-nueces-flow-transition-{stamp}"
    result = analyze_lower_nueces_flow_transition_contrast(
        args.csv.resolve(),
        args.index.resolve(),
        output_dir,
        start=args.start,
        end=args.end,
        min_observations_per_hour=args.min_observations_per_hour,
        max_lag_hours=args.max_lag_hours,
        min_paired_hours=args.min_paired_hours,
        percentile_step=args.percentile_step,
        min_transition_percentile=args.min_transition_percentile,
        max_transition_percentile=args.max_transition_percentile,
        coherence_r=args.coherence_r,
        strong_r=args.strong_r,
        max_lower_r=args.max_lower_r,
        confirm_steps=args.confirm_steps,
        band_width_percentile=args.band_width_percentile,
        event_gap_tolerance_hours=args.event_gap_tolerance_hours,
        min_event_high_hours=args.min_event_high_hours,
        event_min_paired_hours=args.event_min_paired_hours,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except QueryError as exc:
        raise SystemExit(
            f"NRHIS lower Nueces flow-transition analysis failed: {exc}"
        ) from exc
