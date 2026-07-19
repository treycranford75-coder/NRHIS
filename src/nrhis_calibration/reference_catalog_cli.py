"""CLI for cataloging calibration reference cases."""

from __future__ import annotations

import argparse

from .reference_catalog import (
    build_reference_catalog,
    filter_catalog,
    write_catalog_json,
)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("reference_root")
    parser.add_argument("--implementation")
    parser.add_argument("--approved-only", action="store_true")
    parser.add_argument("--valid-only", action="store_true")
    parser.add_argument("--require-approved", action="store_true")
    parser.add_argument("--json-output")
    args = parser.parse_args()

    catalog = build_reference_catalog(
        args.reference_root,
        require_approved=args.require_approved,
    )
    catalog = filter_catalog(
        catalog,
        implementation=args.implementation,
        approved=True if args.approved_only else None,
        valid=True if args.valid_only else None,
    )

    print(f"Reference root: {catalog.root}")
    print(f"Cases: {len(catalog.entries)}")

    for entry in catalog.entries:
        status = "valid" if entry.valid else "invalid"
        approval = "approved" if entry.approved else "unapproved"
        print(
            f"- {entry.case_id} | {entry.implementation} | "
            f"{approval} | {status} | artifacts={entry.artifact_count}"
        )
        if entry.validation_error:
            print(f"  error: {entry.validation_error}")

    if args.json_output:
        write_catalog_json(catalog, args.json_output)
        print(f"Catalog JSON: {args.json_output}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
