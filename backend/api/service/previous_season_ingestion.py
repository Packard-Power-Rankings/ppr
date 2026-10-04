"""Validation and normalization for legacy final-season ranking exports."""

from __future__ import annotations

import csv
import io
import math
from dataclasses import dataclass
from typing import Any


PREVIOUS_SEASON_COLUMNS = (
    "team_id",
    "wins",
    "losses",
    "ties",
    "power",
    "overall_rank",
    "recent_opponent_1",
    "recent_opponent_2",
    "recent_opponent_3",
    "recent_opponent_4",
    "recent_opponent_5",
    "div_rank",
)
MAX_PREVIOUS_SEASON_FILE_BYTES = 5 * 1024 * 1024
MAX_PREVIOUS_SEASON_ROWS = 10_000


class PreviousSeasonFileValidationError(ValueError):
    """Raised when a legacy final-season CSV is not safe to import."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


@dataclass(frozen=True)
class PreviousSeasonFile:
    rows: list[dict[str, Any]]


def _whole_number(value: str, field: str, row_number: int) -> int:
    try:
        number = int(value)
    except ValueError as exc:
        raise ValueError(
            f"Row {row_number}: {field} must be a whole number."
        ) from exc
    return number


def _finite_number(value: str, field: str, row_number: int) -> float:
    try:
        number = float(value)
    except ValueError as exc:
        raise ValueError(
            f"Row {row_number}: {field} must be a number."
        ) from exc
    if not math.isfinite(number):
        raise ValueError(f"Row {row_number}: {field} must be finite.")
    return number


def parse_previous_season_csv(content: bytes) -> PreviousSeasonFile:
    """Parse one legacy final-week export by header name."""
    if len(content) > MAX_PREVIOUS_SEASON_FILE_BYTES:
        raise PreviousSeasonFileValidationError([
            "Previous-season file must be 5 MB or smaller."
        ])
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise PreviousSeasonFileValidationError([
            "File must be UTF-8 encoded."
        ]) from exc

    reader = csv.reader(io.StringIO(text, newline=""), skipinitialspace=True)
    try:
        headers = next(reader)
    except StopIteration as exc:
        raise PreviousSeasonFileValidationError([
            "File is empty; required headers are missing."
        ]) from exc
    except csv.Error as exc:
        raise PreviousSeasonFileValidationError([
            f"Unable to parse CSV headers: {exc}."
        ]) from exc

    normalized_headers = [header.strip().lower() for header in headers]
    duplicate_required_headers = [
        column
        for column in PREVIOUS_SEASON_COLUMNS
        if normalized_headers.count(column) > 1
    ]
    if duplicate_required_headers:
        raise PreviousSeasonFileValidationError([
            "File contains duplicate required column headers: "
            + ", ".join(duplicate_required_headers)
            + "."
        ])
    missing_headers = [
        column
        for column in PREVIOUS_SEASON_COLUMNS
        if column not in normalized_headers
    ]
    if missing_headers:
        raise PreviousSeasonFileValidationError([
            "File format is not correct. Missing required headers: "
            + ", ".join(missing_headers)
            + "."
        ])

    column_indexes = {
        column: normalized_headers.index(column)
        for column in PREVIOUS_SEASON_COLUMNS
    }
    rows: list[dict[str, Any]] = []
    errors: list[str] = []
    source_name_rows: dict[str, int] = {}

    for row_number, row in enumerate(reader, start=2):
        if not row or not any(value.strip() for value in row):
            continue
        if len(rows) >= MAX_PREVIOUS_SEASON_ROWS:
            raise PreviousSeasonFileValidationError([
                "Previous-season file cannot contain more than "
                f"{MAX_PREVIOUS_SEASON_ROWS} teams."
            ])
        if len(row) != len(headers):
            errors.append(
                f"Row {row_number}: expected {len(headers)} columns, "
                f"found {len(row)}."
            )
            continue

        values = {
            column: " ".join(row[index].split())
            for column, index in column_indexes.items()
        }
        team_name = values["team_id"]
        if not team_name:
            errors.append(f"Row {row_number}: team_id is required.")
            continue

        normalized_name = team_name.casefold()
        if normalized_name in source_name_rows:
            errors.append(
                f"Row {row_number}: team_id {team_name!r} duplicates row "
                f"{source_name_rows[normalized_name]}."
            )
            continue
        source_name_rows[normalized_name] = row_number

        try:
            parsed = {
                "row_number": row_number,
                "team_id": team_name,
                "wins": _whole_number(values["wins"], "wins", row_number),
                "losses": _whole_number(
                    values["losses"], "losses", row_number
                ),
                "ties": _whole_number(values["ties"], "ties", row_number),
                "power": _finite_number(values["power"], "power", row_number),
                "overall_rank": _whole_number(
                    values["overall_rank"], "overall_rank", row_number
                ),
                "recent_opp": [
                    _whole_number(
                        values[f"recent_opponent_{position}"],
                        f"recent_opponent_{position}",
                        row_number,
                    )
                    for position in range(1, 6)
                ],
                "division_rank": _whole_number(
                    values["div_rank"], "div_rank", row_number
                ),
            }
        except ValueError as exc:
            errors.append(str(exc))
            continue

        if parsed["wins"] < 0 or parsed["losses"] < 0 or parsed["ties"] < 0:
            errors.append(
                f"Row {row_number}: wins, losses, and ties cannot be negative."
            )
            continue
        if any(opponent_id < 0 for opponent_id in parsed["recent_opp"]):
            errors.append(
                f"Row {row_number}: recent opponent IDs cannot be negative."
            )
            continue
        rows.append(parsed)

    if errors:
        raise PreviousSeasonFileValidationError(errors)
    if not rows:
        raise PreviousSeasonFileValidationError([
            "File does not contain any previous-season rows."
        ])

    return PreviousSeasonFile(rows=rows)
