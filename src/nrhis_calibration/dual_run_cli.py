"""CLI for controlled dual-run calibration verification."""

from __future__ import annotations

import argparse

from .dual_run import run_dual_verification, write_dual_run_summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest")
    parser.add_argument("output_root")
    parser.add_argument("--implementation", default="legacy-pass1")
    parser.add_argument("--timeout-seconds", type=float)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--allow-unapproved", action="store_true")
    parser.add_argument("--summary-output")
    parser.add_argument("extra_args", nargs="*")
    args = parser.parse_args()

    result = run_dual_verification(
        manifest_path=args.manifest,
        output_root=args.output_root,
        implementation=args.implementation,
        extra_args=tuple(args.extra_args),
        timeout_seconds=args.timeout_seconds,
        dry_run=args.dry_run,
        require_approved=not args.allow_unapproved,
    )

    print(f"Case ID: {result.case_id}")
    print(f"Implementation: {result.implementation}")
    print(f"Run ID: {result.run_result.run_id}")
    print(f"Run succeeded: {result.run_result.succeeded}")
    print(f"Matched: {result.matched}")
    print(f"Comparison report: {result.comparison_report_path}")

    if args.summary_output:
        write_dual_run_summary(result, args.summary_output)
        print(f"Dual-run summary: {args.summary_output}")

    return 0 if result.matched else 1


if __name__ == "__main__":
    raise SystemExit(main())
