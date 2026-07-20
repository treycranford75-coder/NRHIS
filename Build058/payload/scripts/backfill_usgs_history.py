from __future__ import annotations

import argparse
import json
from datetime import date
from pathlib import Path

from nrhis_harvest.usgs_historical_backfill import backfill


def main() -> int:
    parser = argparse.ArgumentParser(description="Backfill NRHIS USGS basin observations")
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--start-date", default="2024-02-01")
    parser.add_argument("--end-date", default=date.today().isoformat())
    parser.add_argument("--chunk-days", type=int, default=7)
    parser.add_argument("--timeout-seconds", type=int, default=60)
    parser.add_argument("--no-resume", action="store_true")
    args = parser.parse_args()
    receipt = backfill(
        args.config,
        args.output_root,
        start_date=args.start_date,
        end_date=args.end_date,
        chunk_days=args.chunk_days,
        timeout_seconds=args.timeout_seconds,
        resume=not args.no_resume,
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
