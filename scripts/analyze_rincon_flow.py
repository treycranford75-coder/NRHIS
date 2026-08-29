from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_src = Path(__file__).resolve().parents[1] / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from nrhis_analysis.rincon_flow_analysis import (  # noqa: E402
    DEFAULT_CADENCE_MINUTES,
    DEFAULT_GAP_HOURS,
    DEFAULT_SITE_NO,
    DEFAULT_STAGE_CONTINUITY_RATIO,
    analyze_rincon_flow,
)
from nrhis_analysis.usgs_history_query import QueryError  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analyze Rincon Bayou discharge gaps and directional flow from the local NRHIS archive."
    )
    parser.add_argument("--csv", required=True, type=Path)
    parser.add_argument("--index", required=True, type=Path)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--site", default=DEFAULT_SITE_NO)
    parser.add_argument("--output-root", required=True, type=Path)
    parser.add_argument("--cadence-minutes", type=int, default=DEFAULT_CADENCE_MINUTES)
    parser.add_argument("--gap-hours", type=float, default=DEFAULT_GAP_HOURS)
    parser.add_argument(
        "--stage-continuity-ratio",
        type=float,
        default=DEFAULT_STAGE_CONTINUITY_RATIO,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = args.output_root.resolve() / f"rincon-flow-{stamp}"
    receipt = analyze_rincon_flow(
        args.csv.resolve(),
        args.index.resolve(),
        output_dir,
        start=args.start,
        end=args.end,
        site_no=args.site,
        cadence_minutes=args.cadence_minutes,
        gap_hours=args.gap_hours,
        stage_continuity_ratio=args.stage_continuity_ratio,
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except QueryError as exc:
        raise SystemExit(f"NRHIS Rincon flow analysis failed: {exc}") from exc
