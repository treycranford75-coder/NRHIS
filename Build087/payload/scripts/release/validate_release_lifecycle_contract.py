from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ContractFailure:
    capability_id: str
    missing_patterns: tuple[str, ...]


def load_contract(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1:
        raise ValueError("Unsupported release-lifecycle contract schema version")
    if not isinstance(data.get("required_capabilities"), list):
        raise ValueError("Contract must define required_capabilities")
    return data


def validate_contract(repo_root: Path, contract_path: Path) -> list[ContractFailure]:
    contract = load_contract(contract_path)
    target = repo_root / str(contract["target"])
    text = target.read_text(encoding="utf-8")
    failures: list[ContractFailure] = []

    for capability in contract["required_capabilities"]:
        capability_id = str(capability["id"])
        patterns = tuple(str(item) for item in capability.get("all_patterns", []))
        missing = tuple(pattern for pattern in patterns if pattern not in text)
        if missing:
            failures.append(ContractFailure(capability_id, missing))

    return failures


def write_receipt(path: Path, contract_path: Path, failures: list[ContractFailure]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "contract": str(contract_path),
        "status": "passed" if not failures else "failed",
        "failure_count": len(failures),
        "failures": [
            {
                "capability_id": failure.capability_id,
                "missing_patterns": list(failure.missing_patterns),
            }
            for failure in failures
        ],
    }
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the NRHIS release lifecycle contract")
    parser.add_argument("--repository-root", type=Path, default=Path.cwd())
    parser.add_argument(
        "--contract",
        type=Path,
        default=Path("scripts/release/release-lifecycle-contract.json"),
    )
    parser.add_argument(
        "--receipt",
        type=Path,
        default=Path("data/nrhis/release/lifecycle-contract-validation.json"),
    )
    args = parser.parse_args()

    repo_root = args.repository_root.resolve()
    contract_path = args.contract
    if not contract_path.is_absolute():
        contract_path = repo_root / contract_path
    receipt_path = args.receipt
    if not receipt_path.is_absolute():
        receipt_path = repo_root / receipt_path

    failures = validate_contract(repo_root, contract_path)
    write_receipt(receipt_path, contract_path, failures)

    if failures:
        for failure in failures:
            print(f"FAIL {failure.capability_id}: missing {', '.join(failure.missing_patterns)}")
        return 1

    print("NRHIS release lifecycle contract passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
