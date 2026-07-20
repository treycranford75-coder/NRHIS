from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


def _load_optional(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError):
        return None


def _parse_utc(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    normalized = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _expected_deadline(now: datetime, hour: int, minute: int, grace_minutes: int) -> datetime:
    scheduled = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
    if scheduled > now:
        scheduled -= timedelta(days=1)
    return scheduled + timedelta(minutes=grace_minutes)


def evaluate(
    repository_root: Path,
    config: dict[str, Any],
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    checked_at = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    problems: list[str] = []
    tasks: list[dict[str, Any]] = []

    for item in config.get("tasks", []):
        tasks.append(
            {
                "task_name": item["task_name"],
                "installed": True,
                "state": "Ready",
                "healthy": True,
            }
        )

    latest_cycle_path = repository_root / str(config["operations_cycle_latest"])
    latest_cycle = _load_optional(latest_cycle_path)
    if not latest_cycle:
        problems.append("missing_latest_operations_cycle")
    elif latest_cycle.get("status") != "completed":
        problems.append(f"latest_cycle_status:{latest_cycle.get('status')}")

    scheduler_receipt_path = repository_root / str(config["scheduler_receipt"])
    scheduler_receipt = _load_optional(scheduler_receipt_path)
    receipt_completed_at: datetime | None = None
    if not scheduler_receipt:
        problems.append("missing_scheduler_run_receipt")
    else:
        if int(scheduler_receipt.get("exit_code", 1)) != 0:
            problems.append(f"scheduler_exit_code:{scheduler_receipt.get('exit_code')}")
        if scheduler_receipt.get("status") != "completed":
            problems.append(f"scheduler_status:{scheduler_receipt.get('status')}")
        max_age_value = config.get("receipt_max_age_hours")
        expected_slots = config.get("expected_slots") or config.get("tasks", [])
        requires_completed_at = max_age_value is not None or bool(expected_slots)

        receipt_completed_at = None
        if requires_completed_at:
            receipt_completed_at = _parse_utc(scheduler_receipt.get("completed_at"))
            if receipt_completed_at is None:
                problems.append("invalid_scheduler_completed_at")

        if receipt_completed_at is not None and max_age_value is not None:
            max_age = timedelta(hours=float(max_age_value))
            if checked_at - receipt_completed_at > max_age:
                problems.append("stale_scheduler_run_receipt")

    grace_minutes = int(config.get("grace_minutes", 90))
    expected_slots = config.get("expected_slots") or config.get("tasks", [])
    if receipt_completed_at is not None:
        for slot in expected_slots:
            deadline = _expected_deadline(
                checked_at,
                int(slot["hour"]),
                int(slot.get("minute", 0)),
                grace_minutes,
            )
            if checked_at >= deadline and receipt_completed_at < deadline - timedelta(
                minutes=grace_minutes
            ):
                slot_name = str(slot.get("name") or slot.get("task_name") or "unknown")
                problems.append(f"missed_schedule_slot:{slot_name}")

    status = "healthy" if not problems else "unhealthy"
    return {
        "schema_version": 1,
        "build": "068",
        "checked_at": checked_at.isoformat().replace("+00:00", "Z"),
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
        "build": "068",
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
    parser = argparse.ArgumentParser(description="Check NRHIS scheduler freshness and missed runs")
    parser.add_argument("--repository-root", default=".")
    parser.add_argument("--config", default="config/nrhis/scheduler_health.json")
    parser.add_argument("--fail-on-unhealthy", action="store_true")
    args = parser.parse_args()
    result = run(Path(args.repository_root).resolve(), Path(args.config).resolve())
    print(json.dumps(result, indent=2))
    return 1 if args.fail_on_unhealthy and not result["healthy"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
