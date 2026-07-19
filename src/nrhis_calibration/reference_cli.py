"""CLI for validating calibration reference-case manifests."""

from __future__ import annotations

import argparse
from pathlib import Path

from .reference_cases import load_reference_case, validate_reference_case


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("--require-approved", action="store_true")
    args = parser.parse_args()

    manifest_path = Path(args.manifest).resolve()
    reference_case = load_reference_case(manifest_path)
    verified = validate_reference_case(
        reference_case,
        manifest_directory=manifest_path.parent,
        require_approved=args.require_approved,
    )

    print(f"Case ID: {reference_case.case_id}")
    print(f"Implementation: {reference_case.implementation}")
    print(f"Approved: {reference_case.approved}")
    print(f"Verified artifacts: {len(verified)}")
    for item in verified:
        print(f"  - {item}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
