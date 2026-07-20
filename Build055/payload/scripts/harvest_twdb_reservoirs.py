from __future__ import annotations

import argparse
import json
from pathlib import Path

from nrhis_harvest.twdb_reservoir_harvest import harvest


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Harvest Choke Canyon and Lake Corpus Christi reservoir conditions"
    )
    parser.add_argument(
        "--config", type=Path, default=Path("config/nrhis/twdb_reservoirs_nueces.json")
    )
    parser.add_argument("--data-root", type=Path, default=Path("data/nrhis"))
    parser.add_argument("--timeout-seconds", type=int, default=None)
    args = parser.parse_args()
    receipt = harvest(args.config, args.data_root, timeout_seconds=args.timeout_seconds)
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
