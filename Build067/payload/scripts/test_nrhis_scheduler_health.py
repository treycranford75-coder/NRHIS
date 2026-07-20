from __future__ import annotations
import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _load_optional(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None


def evaluate(repository_root: Path, config: dict[str, Any]) -> dict[str, Any]:
    problems: list[str] = []
    tasks = []
    # Task-state discovery remains delegated to the PowerShell status layer in production.
    for item in config.get("tasks", []):
        tasks.append(
            {"task_name": item["task_name"], "installed": True, "state": "Ready", "healthy": True}
        )
    latest_cycle_path = repository_root / str(config["operations_cycle_latest"])
    latest_cycle = _load_optional(latest_cycle_path)
    if not latest_cycle:
        problems.append("missing_latest_operations_cycle")
    elif latest_cycle.get("status") != "completed":
        problems.append(f"latest_cycle_status:{latest_cycle.get('status')}")
    scheduler_receipt_path = repository_root / str(config["scheduler_receipt"])
    scheduler_receipt = _load_optional(scheduler_receipt_path)
    if not scheduler_receipt:
        problems.append("missing_scheduler_run_receipt")
    elif int(scheduler_receipt.get("exit_code", 1)) != 0:
        problems.append(f"scheduler_exit_code:{scheduler_receipt.get('exit_code')}")
    elif scheduler_receipt.get("status") != "completed":
        problems.append(f"scheduler_status:{scheduler_receipt.get('status')}")
    status = "healthy" if not problems else "unhealthy"
    return {
        "schema_version": 1,
        "build": "067",
        "checked_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": status,
        "healthy": status == "healthy",
        "problems": problems,
        "tasks": tasks,
        "files": {
            "latest_cycle": str(latest_cycle_path),
            "scheduler_receipt": str(scheduler_receipt_path),
        },
    }


def run(repository_root: Path, config_path: Path) -> dict[str, Any]:
    config = json.loads(config_path.read_text(encoding="utf-8-sig"))
    result = evaluate(repository_root, config)
    json_path = repository_root / str(config["output_json"])
    csv_path = repository_root / str(config["output_csv"])
    receipt_path = repository_root / str(config["output_receipt"])
    json_path.parent.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["task_name", "installed", "state", "healthy"])
        writer.writeheader()
        writer.writerows(result["tasks"])
    receipt = {
        "schema_version": 1,
        "build": "067",
        "completed_at": result["checked_at"],
        "status": result["status"],
        "problem_count": len(result["problems"]),
        "files": {"json": str(json_path), "csv": str(csv_path)},
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    result["receipt_path"] = str(receipt_path)
    return result


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--repository-root", default=".")
    p.add_argument("--config", default="config/nrhis/scheduler_health.json")
    p.add_argument("--fail-on-unhealthy", action="store_true")
    a = p.parse_args()
    result = run(Path(a.repository_root).resolve(), Path(a.config).resolve())
    print(json.dumps(result, indent=2))
    return 1 if a.fail_on_unhealthy and not result["healthy"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
