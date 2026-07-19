"""CLI for capturing successful calibration runs as unapproved reference cases."""

from __future__ import annotations

import argparse

from .reference_capture import capture_reference_case


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("run_directory")
    parser.add_argument("reference_root")
    parser.add_argument("case_id")
    parser.add_argument("--description", required=True)
    parser.add_argument("--implementation", default="legacy-pass1")
    args = parser.parse_args()

    result = capture_reference_case(
        run_directory=args.run_directory,
        reference_root=args.reference_root,
        case_id=args.case_id,
        description=args.description,
        implementation=args.implementation,
    )

    print(f"Case directory: {result.case_directory}")
    print(f"Manifest: {result.manifest_path}")
    print(f"Captured artifacts: {len(result.artifact_paths)}")
    print("Approval state: False")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
