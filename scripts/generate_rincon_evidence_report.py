from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_src = Path(__file__).resolve().parents[1] / "src"
if str(_src) not in sys.path:
    sys.path.insert(0, str(_src))

from nrhis_analysis.rincon_evidence_report import build_rincon_evidence_report  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate the formal NRHIS Rincon evidence report.")
    parser.add_argument("--build099-summary", required=True)
    parser.add_argument("--build099-receipt", required=True)
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--title", default="NRHIS Rincon Bayou Evidence Report")
    args = parser.parse_args()

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output_dir = Path(args.output_root) / f"rincon-evidence-report-{stamp}"
    receipt = build_rincon_evidence_report(
        Path(args.build099_summary),
        Path(args.build099_receipt),
        output_dir,
        title=args.title,
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
