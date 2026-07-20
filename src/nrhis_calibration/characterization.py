"""Characterization utilities for calibration reference artifacts."""

from __future__ import annotations

import csv
import hashlib
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence


@dataclass(frozen=True)
class NumericTolerance:
    absolute: float = 0.0
    relative: float = 0.0

    def accepts(self, expected: float, actual: float) -> bool:
        return math.isclose(
            actual,
            expected,
            rel_tol=self.relative,
            abs_tol=self.absolute,
        )


@dataclass(frozen=True)
class CharacterizationDifference:
    location: str
    expected: Any
    actual: Any
    reason: str


@dataclass(frozen=True)
class CharacterizationReport:
    matched: bool
    differences: tuple[CharacterizationDifference, ...]


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def load_json(path: str | Path) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_csv_rows(path: str | Path) -> list[dict[str, str]]:
    with Path(path).open("r", encoding="utf-8", newline="") as source:
        return list(csv.DictReader(source))


def compare_json(
    expected: Any,
    actual: Any,
    *,
    tolerance: NumericTolerance = NumericTolerance(),
    ignored_keys: Iterable[str] = (),
) -> CharacterizationReport:
    ignored = set(ignored_keys)
    differences: list[CharacterizationDifference] = []

    def visit(left: Any, right: Any, location: str) -> None:
        if isinstance(left, Mapping) and isinstance(right, Mapping):
            left_keys = set(left) - ignored
            right_keys = set(right) - ignored
            for missing in sorted(left_keys - right_keys):
                differences.append(
                    CharacterizationDifference(
                        f"{location}.{missing}",
                        left[missing],
                        None,
                        "missing key",
                    )
                )
            for extra in sorted(right_keys - left_keys):
                differences.append(
                    CharacterizationDifference(
                        f"{location}.{extra}",
                        None,
                        right[extra],
                        "unexpected key",
                    )
                )
            for key in sorted(left_keys & right_keys):
                visit(left[key], right[key], f"{location}.{key}")
            return

        if isinstance(left, Sequence) and not isinstance(left, (str, bytes)):
            if not isinstance(right, Sequence) or isinstance(right, (str, bytes)):
                differences.append(
                    CharacterizationDifference(location, left, right, "type mismatch")
                )
                return
            if len(left) != len(right):
                differences.append(
                    CharacterizationDifference(
                        location,
                        len(left),
                        len(right),
                        "sequence length mismatch",
                    )
                )
            for index, (left_item, right_item) in enumerate(zip(left, right)):
                visit(left_item, right_item, f"{location}[{index}]")
            return

        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            if not tolerance.accepts(float(left), float(right)):
                differences.append(
                    CharacterizationDifference(
                        location,
                        left,
                        right,
                        "numeric tolerance exceeded",
                    )
                )
            return

        if left != right:
            differences.append(CharacterizationDifference(location, left, right, "value mismatch"))

    visit(expected, actual, "$")
    return CharacterizationReport(not differences, tuple(differences))


def compare_csv_rows(
    expected_rows: Sequence[Mapping[str, str]],
    actual_rows: Sequence[Mapping[str, str]],
    *,
    key_columns: Sequence[str],
    numeric_columns: Mapping[str, NumericTolerance] | None = None,
) -> CharacterizationReport:
    numeric_columns = numeric_columns or {}
    differences: list[CharacterizationDifference] = []

    def index_rows(rows: Sequence[Mapping[str, str]]) -> dict[tuple[str, ...], Mapping[str, str]]:
        index: dict[tuple[str, ...], Mapping[str, str]] = {}
        for row in rows:
            key = tuple(row[column] for column in key_columns)
            if key in index:
                raise ValueError(f"Duplicate characterization key: {key!r}")
            index[key] = row
        return index

    expected_index = index_rows(expected_rows)
    actual_index = index_rows(actual_rows)

    for missing in sorted(expected_index.keys() - actual_index.keys()):
        differences.append(
            CharacterizationDifference(str(missing), expected_index[missing], None, "missing row")
        )
    for extra in sorted(actual_index.keys() - expected_index.keys()):
        differences.append(
            CharacterizationDifference(str(extra), None, actual_index[extra], "unexpected row")
        )

    for key in sorted(expected_index.keys() & actual_index.keys()):
        expected = expected_index[key]
        actual = actual_index[key]
        columns = set(expected) | set(actual)
        for column in sorted(columns):
            location = f"{key!r}.{column}"
            if column not in expected:
                differences.append(
                    CharacterizationDifference(location, None, actual[column], "unexpected column")
                )
                continue
            if column not in actual:
                differences.append(
                    CharacterizationDifference(location, expected[column], None, "missing column")
                )
                continue

            if column in numeric_columns:
                try:
                    expected_number = float(expected[column])
                    actual_number = float(actual[column])
                except ValueError:
                    differences.append(
                        CharacterizationDifference(
                            location,
                            expected[column],
                            actual[column],
                            "invalid numeric value",
                        )
                    )
                else:
                    if not numeric_columns[column].accepts(expected_number, actual_number):
                        differences.append(
                            CharacterizationDifference(
                                location,
                                expected[column],
                                actual[column],
                                "numeric tolerance exceeded",
                            )
                        )
            elif expected[column] != actual[column]:
                differences.append(
                    CharacterizationDifference(
                        location,
                        expected[column],
                        actual[column],
                        "value mismatch",
                    )
                )

    return CharacterizationReport(not differences, tuple(differences))
