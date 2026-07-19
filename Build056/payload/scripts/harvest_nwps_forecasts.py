from __future__ import annotations

import argparse
import json
from pathlib import Path

from nrhis_harvest.nwps_forecast_harvest import harvest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Harvest NOAA/NWS NWPS forecasts and flood thresholds for NRHIS."
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--timeout-seconds", type=int)
    args = parser.parse_args()
    receipt = harvest(args.config, args.output_root, timeout_seconds=args.timeout_seconds)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
