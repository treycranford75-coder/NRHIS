"""CLI for validating a sprint release inventory."""

from __future__ import annotations

import argparse

from .sprint_closeout import (
    evaluate_sprint_closeout,
    load_release_records,
    write_sprint_closeout_report,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("inventory_json")
    parser.add_argument("--sprint", default="Sprint 2")
    parser.add_argument("--first-build", type=int, required=True)
    parser.add_argument("--final-build", type=int, required=True)
    parser.add_argument("--minimum-coverage", type=float, default=80.0)
    parser.add_argument("--json-output")
    args = parser.parse_args()

    records = load_release_records(args.inventory_json)
    report = evaluate_sprint_closeout(
        sprint=args.sprint,
        records=records,
        expected_first_build=args.first_build,
        expected_final_build=args.final_build,
        minimum_coverage_percent=args.minimum_coverage,
    )

    print(f"Sprint: {report.sprint}")
    print(f"Accepted: {report.accepted}")
    print(f"Releases: {report.release_count}")
    print(f"Build range: {report.first_build}-{report.final_build}")
    for check in report.checks:
        print(f"- {check}")

    if args.json_output:
        write_sprint_closeout_report(report, args.json_output)
        print(f"Closeout JSON: {args.json_output}")

    return 0 if report.accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
