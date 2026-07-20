from __future__ import annotations

import importlib.util
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pytest


def _load_module():
    path = Path("scripts/package_daily_operations_report.py")
    if not path.exists():
        path = Path("payload/scripts/package_daily_operations_report.py")
    spec = importlib.util.spec_from_file_location("build072_package", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _prepare(tmp_path: Path, qa_status: str = "passed") -> Path:
    pub = tmp_path / "data/nrhis/publication"
    pub.mkdir(parents=True)
    (pub / "daily_operations_report.json").write_text(
        json.dumps({"report_date": "2026-07-20", "qa": {"status": qa_status}}),
        encoding="utf-8",
    )
    (pub / "daily_operations_report.md").write_text("# Daily report\n", encoding="utf-8")
    (pub / "daily_operations_report.html").write_text("<h1>Daily report</h1>\n", encoding="utf-8")
    config = tmp_path / "config.json"
    config.write_text(
        json.dumps(
            {
                "publication_root": "data/nrhis/publication/packages",
                "receipt_path": "data/nrhis/receipts/daily_operations_package_receipt.json",
            }
        ),
        encoding="utf-8",
    )
    return config


def test_build072_packages_released_report(tmp_path: Path) -> None:
    module = _load_module()
    config = _prepare(tmp_path)
    now = datetime(2026, 7, 20, 12, 0, tzinfo=timezone.utc)
    result = module.package_report(tmp_path, config, now=now)
    assert result.status == "completed"
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["build"] == "072"
    assert manifest["status"] == "released"
    assert len(manifest["files"]) == 3
    assert all(len(item["sha256"]) == 64 for item in manifest["files"])


def test_build072_blocks_unreleased_report(tmp_path: Path) -> None:
    module = _load_module()
    config = _prepare(tmp_path, qa_status="pending")
    with pytest.raises(RuntimeError, match="not publication-ready"):
        module.package_report(tmp_path, config)


def test_build072_writes_latest_alias_and_history(tmp_path: Path) -> None:
    module = _load_module()
    config = _prepare(tmp_path)
    now = datetime(2026, 7, 20, 18, 0, tzinfo=timezone.utc)
    result = module.package_report(tmp_path, config, now=now)
    root = tmp_path / "data/nrhis/publication/packages"
    assert result.latest_manifest_path == root / "latest_manifest.json"
    assert (root / "latest_package.txt").read_text(encoding="utf-8").strip().endswith(
        "2026-07-20T180000Z"
    )
    assert len((root / "package_history.jsonl").read_text(encoding="utf-8").splitlines()) == 1


def test_build072_override_is_explicit(tmp_path: Path) -> None:
    module = _load_module()
    config = _prepare(tmp_path, qa_status="pending")
    now = datetime(2026, 7, 20, 19, 0, tzinfo=timezone.utc)
    result = module.package_report(tmp_path, config, now=now, allow_unreleased=True)
    manifest = json.loads(result.manifest_path.read_text(encoding="utf-8"))
    assert manifest["status"] == "unreleased_override"
    assert manifest["qa_status"] == "pending"
