"""CLI for creating and validating calibration evidence bundles."""

from __future__ import annotations

import argparse
import json

from .evidence_bundle import create_evidence_bundle, validate_evidence_bundle


def main() -> int:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="action", required=True)

    create = subparsers.add_parser("create")
    create.add_argument("destination_root")
    create.add_argument("bundle_id")
    create.add_argument("artifacts", nargs="+")
    create.add_argument("--metadata-json", default="{}")

    validate = subparsers.add_parser("validate")
    validate.add_argument("manifest")

    args = parser.parse_args()

    if args.action == "create":
        metadata = json.loads(args.metadata_json)
        if not isinstance(metadata, dict):
            raise ValueError("--metadata-json must contain a JSON object")

        result = create_evidence_bundle(
            destination_root=args.destination_root,
            bundle_id=args.bundle_id,
            source_artifacts=args.artifacts,
            metadata=metadata,
        )
        print(f"Bundle directory: {result.bundle_directory}")
        print(f"Manifest: {result.manifest_path}")
        print(f"Artifacts: {result.artifact_count}")
        return 0

    verified = validate_evidence_bundle(args.manifest)
    print(f"Verified artifacts: {len(verified)}")
    for item in verified:
        print(f"- {item}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
