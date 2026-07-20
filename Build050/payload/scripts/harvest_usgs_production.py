from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Harvest current USGS observations for the NRHIS Nueces Basin station set."
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--period", default="P2D")
    parser.add_argument("--timeout", type=int, default=30)
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root / "src"))
    from nrhis_harvest.usgs_basin_harvest import HarvestError, harvest

    try:
        receipt = harvest(
            args.config, args.output_root, period=args.period, timeout_seconds=args.timeout
        )
    except (HarvestError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"USGS harvest failed: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
