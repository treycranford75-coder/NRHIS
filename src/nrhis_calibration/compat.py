"""Compatibility wrapper for the preserved legacy Pass1 calibration flow."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Mapping, Sequence

REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
LEGACY_ROOT = REPOSITORY_ROOT / "src" / "nrhis_calibration" / "legacy"
LEGACY_SCRIPT = LEGACY_ROOT / "calibrate_pass1.py"


class LegacyPass1Error(RuntimeError):
    """Raised when the legacy Pass1 process cannot be prepared or executed."""


@dataclass(frozen=True)
class LegacyPass1Result:
    run_id: str
    command: tuple[str, ...]
    working_directory: str
    started_at_utc: str
    finished_at_utc: str
    duration_seconds: float
    return_code: int
    stdout_path: str
    stderr_path: str
    metadata_path: str
    legacy_script_sha256: str

    @property
    def succeeded(self) -> bool:
        return self.return_code == 0


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _format_run_id(moment: datetime) -> str:
    return moment.strftime("%Y%m%dT%H%M%SZ")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def _validate_legacy_script() -> None:
    if not LEGACY_ROOT.is_dir():
        raise LegacyPass1Error(f"Legacy directory is missing: {LEGACY_ROOT}")
    if not LEGACY_SCRIPT.is_file():
        raise LegacyPass1Error(f"Legacy Pass1 script is missing: {LEGACY_SCRIPT}")


def build_legacy_pass1_command(
    *,
    python_executable: str | Path | None = None,
    extra_args: Sequence[str] = (),
) -> tuple[str, ...]:
    _validate_legacy_script()
    executable = str(python_executable or sys.executable)
    return (executable, str(LEGACY_SCRIPT), *tuple(extra_args))


def run_legacy_pass1(
    *,
    output_root: str | Path,
    python_executable: str | Path | None = None,
    extra_args: Sequence[str] = (),
    environment: Mapping[str, str] | None = None,
    timeout_seconds: float | None = None,
    dry_run: bool = False,
) -> LegacyPass1Result:
    _validate_legacy_script()

    started = _utc_now()
    run_id = _format_run_id(started)
    run_directory = Path(output_root).resolve() / run_id
    run_directory.mkdir(parents=True, exist_ok=False)

    stdout_path = run_directory / "stdout.log"
    stderr_path = run_directory / "stderr.log"
    metadata_path = run_directory / "metadata.json"
    command = build_legacy_pass1_command(
        python_executable=python_executable,
        extra_args=extra_args,
    )

    if dry_run:
        return_code = 0
        stdout_text = "Dry run: command was not executed.\n"
        stderr_text = ""
    else:
        process_environment = os.environ.copy()
        if environment:
            process_environment.update(environment)

        try:
            completed = subprocess.run(
                command,
                cwd=LEGACY_ROOT,
                env=process_environment,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            stdout_text = exc.stdout or ""
            stderr_text = exc.stderr or ""
            return_code = 124
        except OSError as exc:
            raise LegacyPass1Error(f"Unable to start legacy Pass1: {exc}") from exc
        else:
            stdout_text = completed.stdout
            stderr_text = completed.stderr
            return_code = completed.returncode

    finished = _utc_now()
    result = LegacyPass1Result(
        run_id=run_id,
        command=command,
        working_directory=str(LEGACY_ROOT),
        started_at_utc=started.isoformat(),
        finished_at_utc=finished.isoformat(),
        duration_seconds=round((finished - started).total_seconds(), 6),
        return_code=return_code,
        stdout_path=str(stdout_path),
        stderr_path=str(stderr_path),
        metadata_path=str(metadata_path),
        legacy_script_sha256=_sha256(LEGACY_SCRIPT),
    )

    stdout_path.write_text(stdout_text, encoding="utf-8")
    stderr_path.write_text(stderr_text, encoding="utf-8")
    metadata_path.write_text(
        json.dumps({**asdict(result), "succeeded": result.succeeded, "dry_run": dry_run}, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return result
