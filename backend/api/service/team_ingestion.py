"""Validation and normalization for uploaded team metadata CSV files."""

import csv
import io
from pathlib import Path
from typing import Any

TEAM_DATA_COLUMNS = (
    "state",
    "short_name",
    "team_id",
    "long_name",
    "division",
    "conference",
    "ranked",
)
MAX_TEAM_FILE_BYTES = 2 * 1024 * 1024
MAX_TEAM_ROWS = 10_000


def filename_matches_dataset(
    file_name: str,
    sport_type: str,
    gender: str,
    level: str,
) -> bool:
    """Check that a team CSV filename identifies its selected dataset."""
    normalized_name = "".join(
        character for character in Path(file_name).stem.casefold()
        if character.isalnum()
    )
    normalized_sport = "".join(
        character for character in sport_type.casefold() if character.isalnum()
    )
    normalized_level = "".join(
        character for character in level.casefold() if character.isalnum()
    )

    if gender == "womens":
        matches_gender = "womens" in normalized_name or "women" in normalized_name
    else:
        matches_gender = (
            "women" not in normalized_name
            and ("mens" in normalized_name or "men" in normalized_name)
        )

    return (
        normalized_sport in normalized_name
        and normalized_level in normalized_name
        and matches_gender
    )


class TeamFileValidationError(ValueError):
    """Raised when a team metadata CSV does not match its header contract."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


def parse_team_csv(content: bytes) -> list[dict[str, Any]]:
    """Parse team rows by header name, independent of column order."""
    if len(content) > MAX_TEAM_FILE_BYTES:
        raise TeamFileValidationError(["Team file must be 2 MB or smaller."])
    try:
        text = content.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise TeamFileValidationError(["File must be UTF-8 encoded."]) from exc

    reader = csv.reader(io.StringIO(text, newline=""), skipinitialspace=True)
    try:
        headers = next(reader)
    except StopIteration as exc:
        raise TeamFileValidationError(
            ["File is empty; required headers are missing."]) from exc
    except csv.Error as exc:
        raise TeamFileValidationError(
            [f"Unable to parse CSV headers: {exc}."]) from exc

    normalized_headers = [header.strip().lower() for header in headers]
    if len(normalized_headers) != len(set(normalized_headers)):
        raise TeamFileValidationError(
            ["File contains duplicate column headers."])

    missing_headers = [
        column for column in TEAM_DATA_COLUMNS if column not in normalized_headers]
    if missing_headers:
        raise TeamFileValidationError([
            "File format is not correct. Missing required headers: "
            + ", ".join(missing_headers)
            + "."
        ])

    column_indexes = {
        column: normalized_headers.index(column)
        for column in TEAM_DATA_COLUMNS
    }
    teams = []
    errors = []
    team_id_rows = {}

    for row_number, row in enumerate(reader, start=2):
        if not row or not any(value.strip() for value in row):
            continue
        if len(teams) >= MAX_TEAM_ROWS:
            raise TeamFileValidationError([
                f"Team file cannot contain more than {MAX_TEAM_ROWS} teams."
            ])
        if len(row) != len(headers):
            errors.append(
                f"Row {row_number}: expected {len(headers)} columns, found {len(row)}."
            )
            continue

        team = {
            column: " ".join(row[column_indexes[column]].split())
            for column in TEAM_DATA_COLUMNS
        }
        if not team["state"]:
            errors.append(f"Row {row_number}: state is required.")
        if not team["short_name"]:
            errors.append(f"Row {row_number}: short_name is required.")

        if not team["team_id"]:
            errors.append(f"Row {row_number}: team_id is required.")
        else:
            try:
                team["team_id"] = int(team["team_id"])
            except ValueError:
                errors.append(
                    f"Row {row_number}: team_id must be a positive whole number."
                )
            else:
                if team["team_id"] <= 0:
                    errors.append(
                        f"Row {row_number}: team_id must be a positive whole number."
                    )
                elif team["team_id"] in team_id_rows:
                    errors.append(
                        f"Row {row_number}: team_id {team['team_id']} duplicates "
                        f"row {team_id_rows[team['team_id']]}."
                    )
                else:
                    team_id_rows[team["team_id"]] = row_number

        ranked = team["ranked"].casefold()
        if ranked not in {"yes", "no", "true", "false", "1", "0"}:
            errors.append(
                f"Row {row_number}: ranked must be yes or no."
            )
        else:
            team["ranked"] = ranked in {"yes", "true", "1"}
        teams.append(team)

    if errors:
        raise TeamFileValidationError(errors)
    if not teams:
        raise TeamFileValidationError(["File does not contain any team rows."])
    return teams
