"""CLI for creating and validating immutable Sprint archives."""

from __future__ import annotations
import argparse
import json
from .sprint_archive import create_sprint_archive, validate_sprint_archive


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="action", required=True)
    create = subparsers.add_parser("create")
    create.add_argument("destination_root")
    create.add_argument("archive_id")
    create.add_argument("release_inventory")
    create.add_argument("closeout_report")
    create.add_argument("--metadata-json", default="{}")
    validate = subparsers.add_parser("validate")
    validate.add_argument("manifest")
    args = parser.parse_args()
    if args.action == "create":
        metadata = json.loads(args.metadata_json)
        if not isinstance(metadata, dict):
            raise ValueError("--metadata-json must contain a JSON object")
        archive = create_sprint_archive(
            destination_root=args.destination_root,
            archive_id=args.archive_id,
            release_inventory=args.release_inventory,
            closeout_report=args.closeout_report,
            metadata=metadata,
        )
        print(f"Archive directory: {archive.archive_directory}")
        print(f"Manifest: {archive.manifest_path}")
        print(f"Artifacts: {len(archive.artifacts)}")
        return 0
    verified = validate_sprint_archive(args.manifest)
    print(f"Verified artifacts: {len(verified)}")
    for path in verified:
        print(f"- {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
