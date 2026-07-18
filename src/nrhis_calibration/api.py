"""Public calibration API and implementation registry."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .compat import run_legacy_pass1


@dataclass(frozen=True)
class CalibrationRunRequest:
    output_root: str | Path
    implementation: str = "legacy-pass1"
    extra_args: tuple[str, ...] = ()
    timeout_seconds: float | None = None
    dry_run: bool = False


@dataclass(frozen=True)
class CalibrationRunResult:
    implementation: str
    run_id: str
    return_code: int
    succeeded: bool
    metadata_path: str
    stdout_path: str
    stderr_path: str


class CalibrationRunner(Protocol):
    implementation_name: str

    def run(self, request: CalibrationRunRequest) -> CalibrationRunResult:
        ...


class LegacyPass1CalibrationRunner:
    implementation_name = "legacy-pass1"

    def run(self, request: CalibrationRunRequest) -> CalibrationRunResult:
        if request.implementation != self.implementation_name:
            raise ValueError(
                "LegacyPass1CalibrationRunner received incompatible implementation "
                f"{request.implementation!r}"
            )

        legacy_result = run_legacy_pass1(
            output_root=request.output_root,
            extra_args=request.extra_args,
            timeout_seconds=request.timeout_seconds,
            dry_run=request.dry_run,
        )

        return CalibrationRunResult(
            implementation=self.implementation_name,
            run_id=legacy_result.run_id,
            return_code=legacy_result.return_code,
            succeeded=legacy_result.succeeded,
            metadata_path=legacy_result.metadata_path,
            stdout_path=legacy_result.stdout_path,
            stderr_path=legacy_result.stderr_path,
        )


def get_calibration_runner(implementation: str) -> CalibrationRunner:
    normalized = implementation.strip().lower()
    if normalized == "legacy-pass1":
        return LegacyPass1CalibrationRunner()
    raise ValueError(f"Unknown calibration implementation: {implementation!r}")


def run_calibration(request: CalibrationRunRequest) -> CalibrationRunResult:
    return get_calibration_runner(request.implementation).run(request)
