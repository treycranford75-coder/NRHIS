"""CLI for archive retention action manifests."""

from __future__ import annotations

import argparse

from .archive_retention_action import (
    build_action_manifest,
    validate_action_manifest,
    write_action_manifest,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="action", required=True)

    create = subparsers.add_parser("create")
    create.add_argument("plan")
    create.add_argument("approval")
    create.add_argument("output")
    create.add_argument("--live", action="store_true")

    validate = subparsers.add_parser("validate")
    validate.add_argument("plan")
    validate.add_argument("approval")
    validate.add_argument("manifest")

    args = parser.parse_args()

    if args.action == "create":
        manifest = build_action_manifest(
            plan_path=args.plan,
            approval_path=args.approval,
            dry_run=not args.live,
        )
        write_action_manifest(manifest, args.output)
        print(f"Action manifest: {args.output}")
        print(f"Dry run: {manifest.dry_run}")
        print(f"Actions: {len(manifest.actions)}")
        return 0

    manifest = validate_action_manifest(
        plan_path=args.plan,
        approval_path=args.approval,
        action_manifest_path=args.manifest,
    )
    print("Action manifest valid: True")
    print(f"Dry run: {manifest.dry_run}")
    print(f"Actions: {len(manifest.actions)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
