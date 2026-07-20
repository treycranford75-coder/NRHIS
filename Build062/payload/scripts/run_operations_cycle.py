from __future__ import annotations

import argparse
import json
from pathlib import Path

from nrhis_harvest.operations_cycle import run_cycle


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the NRHIS twice-daily operations cycle")
    parser.add_argument("--config", default="config/nrhis/operations_cycle.json")
    parser.add_argument("--repository-root", default=".")
    parser.add_argument("--qa-passes-completed", type=int, default=0)
    parser.add_argument("--cycle-name")
    args = parser.parse_args()
    receipt = run_cycle(
        Path(args.config),
        Path(args.repository_root),
        qa_passes_completed=args.qa_passes_completed,
        cycle_name=args.cycle_name,
    )
    print(json.dumps(receipt, indent=2))
    return 0 if receipt["status"] == "completed" else 1


if __name__ == "__main__":
    raise SystemExit(main())
