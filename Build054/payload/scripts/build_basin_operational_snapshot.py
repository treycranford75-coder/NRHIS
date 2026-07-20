from __future__ import annotations
import argparse
from pathlib import Path
from nrhis_harvest.basin_operational_snapshot import build_snapshot


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build integrated NRHIS basin operational snapshot"
    )
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--output-root", type=Path, required=True)
    args = parser.parse_args()
    receipt = build_snapshot(args.config, args.output_root)
    print(f"Operational snapshot complete: {receipt['receipt_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
