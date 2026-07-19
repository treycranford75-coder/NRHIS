"""CLI for indexing immutable Sprint archives."""

from __future__ import annotations

import argparse

from .sprint_archive_index import (
    build_sprint_archive_index,
    filter_sprint_archive_index,
    write_sprint_archive_index,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("archive_root")
    parser.add_argument("--valid-only", action="store_true")
    parser.add_argument("--sprint")
    parser.add_argument("--json-output")
    args = parser.parse_args()

    index = build_sprint_archive_index(args.archive_root)
    index = filter_sprint_archive_index(
        index,
        valid=True if args.valid_only else None,
        sprint=args.sprint,
    )

    print(f"Archive root: {index.root}")
    print(f"Archives: {len(index.entries)}")

    for entry in index.entries:
        status = "valid" if entry.valid else "invalid"
        print(f"- {entry.archive_id} | {status} | artifacts={entry.artifact_count}")
        if entry.validation_error:
            print(f"  error: {entry.validation_error}")

    if args.json_output:
        write_sprint_archive_index(index, args.json_output)
        print(f"Archive index JSON: {args.json_output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
