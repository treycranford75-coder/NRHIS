"""CLI for archive-retention execution simulations."""

from __future__ import annotations

import argparse

from .archive_retention_execution import (
    simulate_retention_execution,
    validate_execution_report,
    write_execution_report,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="action", required=True)

    simulate = subparsers.add_parser("simulate")
    simulate.add_argument("plan")
    simulate.add_argument("approval")
    simulate.add_argument("action_manifest")
    simulate.add_argument("output")

    validate = subparsers.add_parser("validate")
    validate.add_argument("report")

    args = parser.parse_args()

    if args.action == "simulate":
        report = simulate_retention_execution(
            plan_path=args.plan,
            approval_path=args.approval,
            action_manifest_path=args.action_manifest,
        )
        write_execution_report(report, args.output)
        print(f"Execution report: {args.output}")
        print(f"Dry run: {report.dry_run}")
        print(f"Executed: {report.executed}")
        print(f"Items: {report.item_count}")
        return 0

    report = validate_execution_report(args.report)
    print("Execution report valid: True")
    print(f"Dry run: {report.dry_run}")
    print(f"Executed: {report.executed}")
    print(f"Items: {report.item_count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
