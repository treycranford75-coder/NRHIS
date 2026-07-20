from __future__ import annotations

import argparse
import json
from pathlib import Path

from nrhis_harvest.coastal_salt03_harvest import harvest


def main() -> int:
    parser = argparse.ArgumentParser(description="Harvest SALT03 coastal water-quality observations.")
    parser.add_argument("--config", default="config/nrhis/coastal_salt03.json")
    parser.add_argument("--data-root", default="data/nrhis")
    args = parser.parse_args()
    receipt = harvest(Path(args.config), Path(args.data_root))
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
