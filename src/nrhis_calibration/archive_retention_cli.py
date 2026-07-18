"""CLI for generating Sprint archive retention plans."""
from __future__ import annotations
import argparse
from .archive_retention import build_retention_plan, summarize_retention_plan, write_retention_plan
from .sprint_archive_index import build_sprint_archive_index

def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive_root")
    parser.add_argument("--retain-latest", type=int, default=3)
    parser.add_argument("--json-output")
    args = parser.parse_args()
    index = build_sprint_archive_index(args.archive_root)
    plan = build_retention_plan(index, retain_latest=args.retain_latest)
    summary = summarize_retention_plan(plan)
    print(f"Archives evaluated: {len(plan.decisions)}")
    print(f"Retain: {summary.get('retain', 0)}")
    print(f"Review: {summary.get('review', 0)}")
    print(f"Quarantine: {summary.get('quarantine', 0)}")
    for decision in plan.decisions:
        print(f"- {decision.archive_id}: {decision.action} ({decision.reason})")
    if args.json_output:
        write_retention_plan(plan, args.json_output)
        print(f"Retention plan JSON: {args.json_output}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
