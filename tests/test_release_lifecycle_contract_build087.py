import importlib.util
import sys
import json
from pathlib import Path

MODULE_PATH = Path("scripts/release/validate_release_lifecycle_contract.py")
CONTRACT_PATH = Path("scripts/release/release-lifecycle-contract.json")


def _load_module():
    spec = importlib.util.spec_from_file_location("release_contract_validator", MODULE_PATH)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_contract_manifest_has_expected_capabilities() -> None:
    contract = json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))
    ids = {item["id"] for item in contract["required_capabilities"]}
    assert {
        "pr-state-read",
        "ci-registration-retry",
        "ci-failure-block",
        "automatic-merge",
        "idempotent-branch-cleanup",
        "completion-and-archive",
        "resumable-state",
        "closure-output",
    } <= ids


def test_current_lifecycle_satisfies_structured_contract() -> None:
    module = _load_module()
    failures = module.validate_contract(Path.cwd(), CONTRACT_PATH)
    assert failures == []


def test_validator_reports_missing_capability(tmp_path: Path) -> None:
    module = _load_module()
    target = tmp_path / "scripts/release/Finish-NrhisBuildLifecycle.ps1"
    target.parent.mkdir(parents=True)
    target.write_text("incomplete", encoding="utf-8")
    contract = tmp_path / "contract.json"
    contract.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "target": "scripts/release/Finish-NrhisBuildLifecycle.ps1",
                "required_capabilities": [
                    {"id": "example", "all_patterns": ["required token"]}
                ],
            }
        ),
        encoding="utf-8",
    )
    failures = module.validate_contract(tmp_path, contract)
    assert len(failures) == 1
    assert failures[0].capability_id == "example"
    assert failures[0].missing_patterns == ("required token",)
