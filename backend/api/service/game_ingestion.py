"""Validation and serialization for admin game ingestion."""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from datetime import datetime
from io import StringIO
from typing import Iterable


GAME_COLUMNS = (
    "date",
    "home_team",
    "away_team",
    "home_score",
    "away_score",
    "neutral_site",
)
MAX_GAME_FILE_BYTES = 5 * 1024 * 1024
MAX_GAME_ROWS = 5000
SUPPORTED_DATE_FORMATS = ("%Y-%m-%d", "%m/%d/%Y")


class GameFileValidationError(ValueError):
    """Raised when one or more uploaded game rows are invalid."""

    def __init__(self, errors: list[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


@dataclass(frozen=True)
class GameRow:
    date: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    neutral_site: int

    def as_dict(self) -> dict:
        return asdict(self)


def normalize_team_name(value: str) -> str:
    """Remove accidental surrounding and repeated whitespace from a team name."""
    return " ".join(str(value).split())


def normalized_date(value: str) -> str:
    """Validate supported date formats and return a stable ISO identity value."""
    candidate = str(value).strip()
    for date_format in SUPPORTED_DATE_FORMATS:
        try:
            return datetime.strptime(candidate, date_format).date().isoformat()
        except ValueError:
            continue
    raise ValueError("date must use YYYY-MM-DD or MM/DD/YYYY")


def game_identity(date: str, home_team: str, away_team: str) -> str:
    """Return a case-insensitive identity independent of home/away ordering."""
    participants = sorted((
        normalize_team_name(home_team).casefold(),
        normalize_team_name(away_team).casefold(),
    ))
    return "|".join((normalized_date(date), *participants))


def canonical_game_identity(date: str, home_team_id: int, away_team_id: int) -> str:
    """Return a rename-safe identity independent of home/away ordering."""
    participants = sorted((int(home_team_id), int(away_team_id)))
    return f"{normalized_date(date)}|{participants[0]}|{participants[1]}"


def canonical_game_id(date: str, home_team_id: int, away_team_id: int) -> str:
    """Return the ID used by canonical and materialized game records."""
    return f"{int(home_team_id)}_{int(away_team_id)}_{normalized_date(date)}"


def _integer(value: str, field: str) -> int:
    candidate = str(value).strip()
    if not candidate or not candidate.isdigit():
        raise ValueError(f"{field} must be a nonnegative integer")
    return int(candidate)


def validate_game_values(values: Iterable[object], row_number: int = 1) -> GameRow:
    """Validate one six-column game row."""
    cells = [str(value).strip() for value in values]
    if len(cells) != len(GAME_COLUMNS):
        raise GameFileValidationError([
            f"Row {row_number}: expected 6 columns, found {len(cells)}"
        ])

    if tuple(value.casefold() for value in cells) == GAME_COLUMNS:
        raise GameFileValidationError([
            f"Row {row_number}: remove the header row; game files are headerless"
        ])

    errors = []
    try:
        normalized_date(cells[0])
    except ValueError as exc:
        errors.append(f"Row {row_number}: {exc}")

    home_team = normalize_team_name(cells[1])
    away_team = normalize_team_name(cells[2])
    if not home_team:
        errors.append(f"Row {row_number}: home_team is required")
    if not away_team:
        errors.append(f"Row {row_number}: away_team is required")
    if home_team and away_team and home_team.casefold() == away_team.casefold():
        errors.append(f"Row {row_number}: home_team and away_team must be different")

    try:
        home_score = _integer(cells[3], "home_score")
    except ValueError as exc:
        errors.append(f"Row {row_number}: {exc}")
        home_score = 0

    try:
        away_score = _integer(cells[4], "away_score")
    except ValueError as exc:
        errors.append(f"Row {row_number}: {exc}")
        away_score = 0

    try:
        neutral_site = _integer(cells[5], "neutral_site")
        if neutral_site not in (0, 999):
            raise ValueError("neutral_site must be 0 or 999")
    except ValueError as exc:
        errors.append(f"Row {row_number}: {exc}")
        neutral_site = 0

    if errors:
        raise GameFileValidationError(errors)

    return GameRow(
        date=cells[0],
        home_team=home_team,
        away_team=away_team,
        home_score=home_score,
        away_score=away_score,
        neutral_site=neutral_site,
    )


def parse_game_csv(file_content: bytes | str) -> list[GameRow]:
    """Parse and fully validate a headerless game CSV."""
    if isinstance(file_content, bytes):
        if len(file_content) > MAX_GAME_FILE_BYTES:
            raise GameFileValidationError(["Game file must be 5 MB or smaller"])
        try:
            text = file_content.decode("utf-8-sig")
        except UnicodeDecodeError as exc:
            raise GameFileValidationError([
                "Game file must be UTF-8 encoded"
            ]) from exc
    else:
        text = file_content.lstrip("\ufeff")
        if len(text.encode("utf-8")) > MAX_GAME_FILE_BYTES:
            raise GameFileValidationError(["Game file must be 5 MB or smaller"])

    try:
        raw_rows = [row for row in csv.reader(StringIO(text)) if any(
            str(cell).strip() for cell in row
        )]
    except csv.Error as exc:
        raise GameFileValidationError([f"Invalid CSV: {exc}"]) from exc

    if not raw_rows:
        raise GameFileValidationError(["Game file does not contain any games"])
    if len(raw_rows) > MAX_GAME_ROWS:
        raise GameFileValidationError([
            f"Game file cannot contain more than {MAX_GAME_ROWS} games"
        ])

    games: list[GameRow] = []
    errors: list[str] = []
    identities: dict[str, int] = {}
    for row_number, raw_row in enumerate(raw_rows, start=1):
        try:
            game = validate_game_values(raw_row, row_number)
            identity = game_identity(game.date, game.home_team, game.away_team)
            if identity in identities:
                errors.append(
                    f"Row {row_number}: duplicates row {identities[identity]}"
                )
                continue
            identities[identity] = row_number
            games.append(game)
        except GameFileValidationError as exc:
            errors.extend(exc.errors)

    if errors:
        raise GameFileValidationError(errors)
    return games


def serialize_game_rows(games: Iterable[GameRow]) -> bytes:
    """Serialize validated game rows using the application's headerless contract."""
    output = StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    for game in games:
        writer.writerow([
            game.date,
            game.home_team,
            game.away_team,
            game.home_score,
            game.away_score,
            game.neutral_site,
        ])
    return output.getvalue().encode("utf-8")
