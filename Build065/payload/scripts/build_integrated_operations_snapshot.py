from __future__ import annotations

import argparse
import json
from pathlib import Path

from nrhis_harvest.integrated_operations_snapshot import run


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/nrhis/integrated_operations_snapshot.json")
    parser.add_argument("--data-root", default="data/nrhis")
    args = parser.parse_args()
    print(json.dumps(run(Path(args.config), Path(args.data_root)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
