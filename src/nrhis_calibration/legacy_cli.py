"""Command-line adapter for the legacy Pass1 compatibility wrapper."""

from __future__ import annotations

import argparse

from .compat import run_legacy_pass1


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", required=True)
    parser.add_argument("--timeout-seconds", type=float)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--extra-arg", action="append", default=[])
    args = parser.parse_args()

    result = run_legacy_pass1(
        output_root=args.output_root,
        extra_args=tuple(args.extra_arg),
        timeout_seconds=args.timeout_seconds,
        dry_run=args.dry_run,
    )

    print(f"Run ID: {result.run_id}")
    print(f"Return code: {result.return_code}")
    print(f"Metadata: {result.metadata_path}")
    print(f"Stdout: {result.stdout_path}")
    print(f"Stderr: {result.stderr_path}")

    return result.return_code


if __name__ == "__main__":
    raise SystemExit(main())
