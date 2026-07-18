"""CLI for approving or revoking calibration reference cases."""

from __future__ import annotations

import argparse

from .reference_approval import approve_reference_case, revoke_reference_case


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="action", required=True)

    approve = subparsers.add_parser("approve")
    approve.add_argument("manifest")
    approve.add_argument("--reviewer", required=True)
    approve.add_argument("--rationale", required=True)

    revoke = subparsers.add_parser("revoke")
    revoke.add_argument("manifest")
    revoke.add_argument("--reviewer", required=True)
    revoke.add_argument("--rationale", required=True)

    args = parser.parse_args()

    if args.action == "approve":
        record = approve_reference_case(
            args.manifest,
            reviewer=args.reviewer,
            rationale=args.rationale,
        )
    else:
        record = revoke_reference_case(
            args.manifest,
            reviewer=args.reviewer,
            rationale=args.rationale,
        )

    print(f"Case ID: {record.case_id}")
    print(f"Action: {record.action}")
    print(f"Reviewer: {record.reviewer}")
    print(f"Timestamp: {record.timestamp_utc}")
    print(f"Record: {record.approval_record_path}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
