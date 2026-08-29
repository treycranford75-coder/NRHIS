from __future__ import annotations

import argparse
import json
from pathlib import Path

from nrhis_harvest.usgs_historical_backfill import finalize_completed_archive


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Finalize an already-complete NRHIS USGS historical archive without network requests"
    )
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--start-date", required=True)
    parser.add_argument("--end-date", required=True)
    args = parser.parse_args()

    receipt = finalize_completed_archive(
        args.output_root,
        start_date=args.start_date,
        end_date=args.end_date,
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
