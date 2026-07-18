"""CLI for evaluating calibration release evidence."""

from __future__ import annotations

import argparse

from .release_gate import evaluate_release_gate, write_release_gate_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("release_id")
    parser.add_argument("evidence_manifest")
    parser.add_argument("--allow-mismatch", action="store_true")
    parser.add_argument("--json-output")
    args = parser.parse_args()

    report = evaluate_release_gate(
        release_id=args.release_id,
        evidence_manifest=args.evidence_manifest,
        require_matched_comparison=not args.allow_mismatch,
    )

    print(f"Release ID: {report.release_id}")
    print(f"Accepted: {report.accepted}")
    print(f"Evidence manifest: {report.evidence_manifest}")
    for check in report.checks:
        status = "PASS" if check.passed else "FAIL"
        print(f"- {status} {check.name}: {check.detail}")

    if args.json_output:
        write_release_gate_report(report, args.json_output)
        print(f"Release gate JSON: {args.json_output}")

    return 0 if report.accepted else 1


if __name__ == "__main__":
    raise SystemExit(main())
