"""CLI for controlled reference-case comparison."""

from __future__ import annotations

import argparse

from .comparison_runner import compare_reference_case, write_comparison_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("candidate_root")
    parser.add_argument("--allow-unapproved", action="store_true")
    parser.add_argument("--json-output")
    args = parser.parse_args()

    report = compare_reference_case(
        args.manifest,
        candidate_root=args.candidate_root,
        require_approved=not args.allow_unapproved,
    )

    print(f"Case ID: {report.case_id}")
    print(f"Implementation: {report.implementation}")
    print(f"Matched: {report.matched}")
    print(f"Artifacts compared: {len(report.artifact_reports)}")

    for item in report.artifact_reports:
        status = "matched" if item.matched else "different"
        print(f"- {item.candidate_path}: {status}")
        for difference in item.differences:
            print(f"  {difference.location}: {difference.reason}")

    if args.json_output:
        write_comparison_report(report, args.json_output)
        print(f"Comparison JSON: {args.json_output}")

    return 0 if report.matched else 1


if __name__ == "__main__":
    raise SystemExit(main())
