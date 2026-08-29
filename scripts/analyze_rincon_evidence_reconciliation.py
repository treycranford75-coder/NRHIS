from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_src = Path(__file__).resolve().parents[1] / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from nrhis_analysis.rincon_evidence_reconciliation import (  # noqa: E402
    analyze_rincon_evidence_reconciliation,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Reconcile Build097 negative-observation intervals with Build098 "
            "integrated reverse-flow intervals and emit a critical Rincon evidence timeline."
        )
    )
    parser.add_argument("--csv", required=True)
    parser.add_argument("--index", required=True)
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--site", default="08211503")
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--cadence-minutes", type=int, default=15)
    parser.add_argument("--gap-hours", type=float, default=24.0)
    args = parser.parse_args()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = Path(args.output_root) / f"rincon-evidence-{stamp}"
    receipt = analyze_rincon_evidence_reconciliation(
        Path(args.csv),
        Path(args.index),
        output_dir,
        start=args.start,
        end=args.end,
        site_no=args.site,
        cadence_minutes=args.cadence_minutes,
        gap_hours=args.gap_hours,
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
