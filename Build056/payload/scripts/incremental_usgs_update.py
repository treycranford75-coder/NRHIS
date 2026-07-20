from __future__ import annotations

import argparse
import json
from datetime import date, datetime, timezone
from pathlib import Path

from nrhis_harvest.usgs_incremental_update import incremental_update


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run restart-safe incremental USGS update and quality checks."
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--end-date", default=date.today().isoformat())
    parser.add_argument("--study-start", default="2024-02-01")
    parser.add_argument("--overlap-days", type=int, default=2)
    parser.add_argument("--chunk-days", type=int, default=2)
    parser.add_argument("--lookback-days", type=int, default=7)
    parser.add_argument("--gap-minutes", type=int, default=120)
    args = parser.parse_args()
    receipt = incremental_update(
        args.config,
        args.output_root,
        end_date=args.end_date,
        study_start=args.study_start,
        overlap_days=args.overlap_days,
        chunk_days=args.chunk_days,
        lookback_days=args.lookback_days,
        gap_minutes=args.gap_minutes,
        assessed_at=datetime.now(timezone.utc),
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
