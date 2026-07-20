from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from nrhis_harvest.reservoir_operations_summary import run  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="config/nrhis/reservoir_operations_summary.json")
    parser.add_argument("--data-root", default="data/nrhis")
    args = parser.parse_args()
    print(json.dumps(run(Path(args.config), Path(args.data_root)), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
