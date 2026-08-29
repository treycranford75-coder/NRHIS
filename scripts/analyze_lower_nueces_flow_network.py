from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_src = Path(__file__).resolve().parents[1] / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from nrhis_analysis.lower_nueces_flow_network import (  # noqa: E402
    DEFAULT_SITE_NOS,
    analyze_lower_nueces_flow_network,
)
from nrhis_analysis.usgs_history_query import QueryError  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze lower Nueces station-to-station discharge from the finalized local archive."
    )
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--index", required=True, type=Path)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--min-observations-per-hour", type=int, default=2)
    parser.add_argument("--max-lag-hours", type=int, default=72)
    parser.add_argument("--min-paired-hours", type=int, default=48)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = args.output_root.resolve() / f"lower-nueces-flow-{stamp}"
    result = analyze_lower_nueces_flow_network(
        args.csv.resolve(),
        args.index.resolve(),
        output_dir,
        start=args.start,
        end=args.end,
        site_nos=DEFAULT_SITE_NOS,
        min_observations_per_hour=args.min_observations_per_hour,
        max_lag_hours=args.max_lag_hours,
        min_paired_hours=args.min_paired_hours,
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except QueryError as exc:
        raise SystemExit(f"NRHIS lower Nueces analysis failed: {exc}") from exc
