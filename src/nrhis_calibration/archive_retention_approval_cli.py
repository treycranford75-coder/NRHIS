"""CLI for approving and validating archive retention plans."""

from __future__ import annotations

import argparse

from .archive_retention_approval import (
    approve_retention_plan,
    validate_retention_approval,
    write_retention_approval,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="action", required=True)

    approve = subparsers.add_parser("approve")
    approve.add_argument("plan")
    approve.add_argument("approval_output")
    approve.add_argument("--reviewer", required=True)
    approve.add_argument("--rationale", required=True)
    approve.add_argument(
        "--approved-action",
        action="append",
        dest="approved_actions",
    )

    validate = subparsers.add_parser("validate")
    validate.add_argument("plan")
    validate.add_argument("approval")

    args = parser.parse_args()

    if args.action == "approve":
        actions = (
            tuple(args.approved_actions)
            if args.approved_actions
            else ("retain", "review", "quarantine")
        )
        approval = approve_retention_plan(
            plan_path=args.plan,
            reviewer=args.reviewer,
            rationale=args.rationale,
            approved_actions=actions,
        )
        write_retention_approval(approval, args.approval_output)
        print(f"Approval: {args.approval_output}")
        print(f"Reviewer: {approval.reviewer}")
        print(f"Decisions: {approval.decision_count}")
        print(f"Plan SHA-256: {approval.plan_sha256}")
        return 0

    approval = validate_retention_approval(
        plan_path=args.plan,
        approval_path=args.approval,
    )
    print("Approval valid: True")
    print(f"Reviewer: {approval.reviewer}")
    print(f"Decisions: {approval.decision_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
