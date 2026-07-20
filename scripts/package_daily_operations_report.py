from __future__ import annotations

import argparse
import hashlib
import json
import shutil
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REQUIRED_INPUTS = {
    "json": "data/nrhis/publication/daily_operations_report.json",
    "markdown": "data/nrhis/publication/daily_operations_report.md",
    "html": "data/nrhis/publication/daily_operations_report.html",
}


@dataclass(frozen=True)
class PackageResult:
    status: str
    package_dir: Path
    manifest_path: Path
    latest_manifest_path: Path
    receipt_path: Path


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(text, encoding="utf-8", newline="\n")
    temp.replace(path)


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8-sig"))


def _release_status(report: dict[str, Any]) -> tuple[bool, str]:
    qa = report.get("qa") or report.get("quality_assurance") or {}
    status = str(qa.get("status") or report.get("qa_status") or "").strip().lower()
    passed = qa.get("passed")
    if passed is True:
        return True, status or "passed"
    if status in {"passed", "approved", "released", "publication_ready", "complete"}:
        return True, status
    return False, status or "unknown"


def package_report(
    repository_root: Path,
    config_path: Path,
    now: datetime | None = None,
    allow_unreleased: bool = False,
) -> PackageResult:
    repository_root = repository_root.resolve()
    config = _load_json(config_path)
    now = now or datetime.now(timezone.utc)
    stamp = now.strftime("%Y-%m-%dT%H%M%SZ")

    inputs = {
        name: repository_root / str(config.get("inputs", {}).get(name, relative))
        for name, relative in REQUIRED_INPUTS.items()
    }
    missing = [str(path) for path in inputs.values() if not path.is_file()]
    if missing:
        raise FileNotFoundError("Missing daily report inputs: " + ", ".join(missing))

    report = _load_json(inputs["json"])
    released, qa_status = _release_status(report)
    if not released and not allow_unreleased:
        raise RuntimeError(
            f"Daily operations report is not publication-ready; QA status is {qa_status!r}."
        )

    publication_root = repository_root / str(
        config.get("publication_root", "data/nrhis/publication/packages")
    )
    package_dir = publication_root / stamp
    package_dir.mkdir(parents=True, exist_ok=False)

    copied: list[dict[str, Any]] = []
    output_names = config.get("output_names", {})
    for kind, source in inputs.items():
        destination = package_dir / str(
            output_names.get(kind, f"daily_operations_report.{source.suffix.lstrip('.')}")
        )
        shutil.copy2(source, destination)
        copied.append(
            {
                "kind": kind,
                "path": destination.relative_to(repository_root).as_posix(),
                "bytes": destination.stat().st_size,
                "sha256": _sha256(destination),
            }
        )

    manifest = {
        "schema_version": 1,
        "build": "072",
        "created_at": now.isoformat().replace("+00:00", "Z"),
        "status": "released" if released else "unreleased_override",
        "qa_status": qa_status,
        "report_date": report.get("report_date") or report.get("date"),
        "package_id": stamp,
        "files": copied,
    }
    manifest_path = package_dir / "manifest.json"
    _atomic_write(manifest_path, json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    latest_manifest_path = publication_root / "latest_manifest.json"
    _atomic_write(latest_manifest_path, json.dumps(manifest, indent=2, sort_keys=True) + "\n")

    latest_index_path = publication_root / "latest_package.txt"
    _atomic_write(latest_index_path, package_dir.relative_to(repository_root).as_posix() + "\n")

    history_path = publication_root / "package_history.jsonl"
    with history_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(manifest, sort_keys=True) + "\n")

    receipt = {
        "schema_version": 1,
        "build": "072",
        "completed_at": manifest["created_at"],
        "status": "completed",
        "package_dir": package_dir.relative_to(repository_root).as_posix(),
        "manifest": manifest_path.relative_to(repository_root).as_posix(),
        "file_count": len(copied),
    }
    receipt_path = repository_root / str(
        config.get(
            "receipt_path",
            "data/nrhis/receipts/daily_operations_package_receipt.json",
        )
    )
    _atomic_write(receipt_path, json.dumps(receipt, indent=2, sort_keys=True) + "\n")

    return PackageResult(
        status=receipt["status"],
        package_dir=package_dir,
        manifest_path=manifest_path,
        latest_manifest_path=latest_manifest_path,
        receipt_path=receipt_path,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a dated, checksum-verified NRHIS daily operations publication package."
    )
    parser.add_argument("--repository-root", default=".")
    parser.add_argument(
        "--config", default="config/nrhis/daily_operations_package.json"
    )
    parser.add_argument("--allow-unreleased", action="store_true")
    args = parser.parse_args()

    result = package_report(
        Path(args.repository_root),
        Path(args.config),
        allow_unreleased=args.allow_unreleased,
    )
    print(
        json.dumps(
            {
                "status": result.status,
                "package_dir": str(result.package_dir),
                "manifest": str(result.manifest_path),
                "latest_manifest": str(result.latest_manifest_path),
                "receipt": str(result.receipt_path),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
