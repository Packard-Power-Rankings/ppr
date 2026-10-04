"""Generate and serve immutable season ranking snapshots."""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from typing import Any

from fastapi import HTTPException, status
from api.database import sports_database as database


class ArchiveService:
    """Create self-contained public HTML and JSON ranking archives."""

    def __init__(self, sports_collection=None, archive_dir: str | Path | None = None):
        self.sports_collection = sports_collection \
            if sports_collection is not None \
            else database.get_collection("temp2")
        self.archive_dir = Path(
            archive_dir or os.getenv("ARCHIVE_DIR", "/var/lib/ppr-archives")
        )

    @staticmethod
    def current_year() -> int:
        return datetime.now(timezone.utc).year

    @staticmethod
    def _display_name(value: Any) -> str:
        return str(value or "").replace("_", " ").title()

    @classmethod
    def _dataset_label(cls, sport: str, gender: str, level: str) -> str:
        return " ".join(
            cls._display_name(value) for value in (level, gender, sport)
        )

    @staticmethod
    def _dataset_slug(sport: str, gender: str, level: str) -> str:
        raw_slug = "-".join((sport, gender, level)).lower()
        return re.sub(r"[^a-z0-9]+", "-", raw_slug).strip("-") or "rankings"

    @staticmethod
    def _as_int(value: Any) -> int:
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    @staticmethod
    def _as_float(value: Any) -> float | None:
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @classmethod
    def _latest_power(cls, power_ranking: Any) -> tuple[float | None, str]:
        if not isinstance(power_ranking, list):
            return None, ""

        for entry in reversed(power_ranking):
            if not isinstance(entry, dict) or not entry:
                continue
            ranking_date, ranking_value = next(iter(entry.items()))
            return cls._as_float(ranking_value), str(ranking_date)
        return None, ""

    @classmethod
    def _normalize_teams(cls, teams: Any) -> list[dict[str, Any]]:
        normalized = []
        for team in teams if isinstance(teams, list) else []:
            if not isinstance(team, dict):
                continue
            power, power_date = cls._latest_power(team.get("power_ranking"))
            normalized.append({
                "id": cls._as_int(team.get("team_id")),
                "stored_rank": cls._as_int(team.get("overall_rank")),
                "team_name": str(team.get("team_name") or "Unknown Team"),
                "power": power,
                "power_date": power_date,
                "division_rank": cls._as_int(team.get("division_rank")),
                "division": str(team.get("division") or ""),
                "wins": cls._as_int(team.get("wins")),
                "losses": cls._as_int(team.get("losses")),
            })

        def ranking_key(team: dict[str, Any]):
            stored_rank = team["stored_rank"]
            power = team["power"] if team["power"] is not None else float("-inf")
            if stored_rank > 0:
                return 0, stored_rank, -power, team["team_name"].casefold()
            return 1, 0, -power, team["team_name"].casefold()

        normalized.sort(key=ranking_key)
        for team in normalized:
            team["rank"] = (
                team["stored_rank"] if team["stored_rank"] > 0 else 9999
            )
        return normalized

    @staticmethod
    def _dataset_sort_key(dataset: dict[str, Any]):
        sport_order = {"football": 0, "basketball": 1}
        gender_order = {"mens": 0, "womens": 1}
        level_order = {"high_school": 0, "college": 1}
        return (
            sport_order.get(dataset["sport"], 99),
            dataset["sport"],
            gender_order.get(dataset["gender"], 99),
            dataset["gender"],
            level_order.get(dataset["level"], 99),
            dataset["level"],
        )

    async def _current_datasets(
        self,
        year: int,
        dataset_key: tuple[str, str, str] | None = None,
    ) -> list[dict[str, Any]]:
        query = {
            "sport_type": {"$exists": True},
            "gender": {"$exists": True},
            "level": {"$exists": True},
        }
        if dataset_key:
            query = {
                "sport_type": dataset_key[0],
                "gender": dataset_key[1],
                "level": dataset_key[2],
            }
        cursor = self.sports_collection.find(
            query,
            {
                "_id": 0,
                "sport_type": 1,
                "gender": 1,
                "level": 1,
                "teams": 1,
            },
        )
        documents = await cursor.to_list(length=None)
        datasets = []
        for document in documents:
            sport = str(document.get("sport_type") or "").lower()
            gender = str(document.get("gender") or "").lower()
            level = str(document.get("level") or "").lower()
            if not all((sport, gender, level)):
                continue

            slug = self._dataset_slug(sport, gender, level)
            teams = self._normalize_teams(document.get("teams"))
            datasets.append({
                "sport": sport,
                "gender": gender,
                "level": level,
                "label": self._dataset_label(sport, gender, level),
                "slug": slug,
                "team_count": len(teams),
                "url": f"/archives/{year}/{slug}",
                "static_url": f"/archive/{year}/{slug}.html",
                "teams": teams,
            })

        datasets.sort(key=self._dataset_sort_key)
        return datasets

    @staticmethod
    def _archive_summary(archive: dict[str, Any]) -> dict[str, Any]:
        return {
            "year": archive["year"],
            "archived_at": archive["archived_at"],
            "dataset_count": archive["dataset_count"],
            "team_count": archive["team_count"],
            "url": f"/archives/{archive['year']}",
            "static_url": f"/archive/{archive['year']}/index.html",
            "datasets": [
                {key: value for key, value in dataset.items() if key != "teams"}
                for dataset in archive["datasets"]
            ],
        }

    @staticmethod
    def _write_json(path: Path, value: dict[str, Any]):
        path.write_text(
            json.dumps(value, indent=2, ensure_ascii=True) + "\n",
            encoding="utf-8",
        )

    @staticmethod
    def _styles() -> str:
        return """
            :root { color-scheme: light; font-family: Inter, system-ui, sans-serif; }
            * { box-sizing: border-box; }
            body { margin: 0; color: #17202a; background: #f4f6f8; }
            header { background: #17202a; color: #fff; padding: 2rem 1.25rem; }
            header div, main { width: min(1120px, 100%); margin: 0 auto; }
            h1 { margin: 0; font-size: clamp(1.75rem, 4vw, 2.5rem); }
            header p { margin: .5rem 0 0; color: #d6e4f0; }
            main { padding: 1.5rem 1.25rem 3rem; }
            a { color: #075ea8; }
            .back { display: inline-block; margin-bottom: 1rem; font-weight: 600; }
            .datasets { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1rem; }
            .dataset { background: #fff; border: 1px solid #d7dee5; border-radius: 6px; padding: 1rem; }
            .dataset h2 { font-size: 1.1rem; margin: 0 0 .35rem; }
            .dataset p { color: #52616f; margin: 0 0 .75rem; }
            .table-wrap { overflow-x: auto; background: #fff; border: 1px solid #d7dee5; border-radius: 6px; }
            table { width: 100%; border-collapse: collapse; min-width: 760px; }
            th, td { padding: .75rem; border-bottom: 1px solid #e4e9ee; text-align: left; }
            th { background: #eaf0f5; font-size: .78rem; text-transform: uppercase; color: #34495e; }
            tbody tr:last-child td { border-bottom: 0; }
            .rank { font-weight: 700; color: #075ea8; }
            .number { text-align: right; font-variant-numeric: tabular-nums; }
            .empty { background: #fff; border-left: 4px solid #168aad; padding: 1rem; }
            footer { color: #647482; font-size: .85rem; margin-top: 1.25rem; }
        """

    @staticmethod
    def _power_display(power: float | None) -> str:
        return "-" if power is None else f"{power:.2f}"

    @classmethod
    def _render_dataset_page(
        cls,
        year: int,
        archived_at: str,
        dataset: dict[str, Any],
    ) -> str:
        rows = []
        for team in dataset["teams"]:
            rows.append(
                "<tr>"
                f"<td>{team['id']}</td>"
                f"<td class=\"rank\">{team['rank']}</td>"
                f"<td>{escape(team['team_name'])}</td>"
                f"<td class=\"number\">{cls._power_display(team['power'])}</td>"
                f"<td class=\"number\">{team['division_rank'] or '-'}</td>"
                f"<td>{escape(team['division']) or '-'}</td>"
                f"<td class=\"number\">{team['wins']}</td>"
                f"<td class=\"number\">{team['losses']}</td>"
                "</tr>"
            )
        table = (
            '<div class="table-wrap"><table>'
                '<thead><tr><th>Id</th><th>Rank</th><th>Team</th>'
                '<th class="number">Power</th>'
                '<th class="number">Div. Rank</th><th>Division</th>'
            '<th class="number">W</th><th class="number">L</th></tr></thead>'
            f"<tbody>{''.join(rows)}</tbody></table></div>"
            if rows else '<p class="empty">No ranking data was available for this dataset.</p>'
        )
        title = f"{year} {dataset['label']} Rankings"
        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(title)} | Packard Power Rankings</title>
  <style>{cls._styles()}</style>
</head>
<body>
  <header><div><h1>{escape(title)}</h1><p>Archived season standings</p></div></header>
  <main>
    <a class="back" href="index.html">Back to {year} archive</a>
    {table}
    <footer>Snapshot created {escape(archived_at)}</footer>
  </main>
</body>
</html>
"""

    @classmethod
    def _render_year_index(cls, archive: dict[str, Any]) -> str:
        links = []
        for dataset in archive["datasets"]:
            links.append(
                '<article class="dataset">'
                f"<h2>{escape(dataset['label'])}</h2>"
                f"<p>{dataset['team_count']} teams</p>"
                f"<a href=\"{escape(dataset['slug'])}.html\">View rankings</a>"
                "</article>"
            )
        return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{archive['year']} Season Archive | Packard Power Rankings</title>
  <style>{cls._styles()}</style>
</head>
<body>
  <header><div><h1>{archive['year']} Season Archive</h1><p>Packard Power Rankings</p></div></header>
  <main>
    <div class="datasets">{''.join(links)}</div>
    <footer>Snapshot created {escape(archive['archived_at'])}</footer>
  </main>
</body>
</html>
"""

    def _read_archive(self, year: int) -> dict[str, Any] | None:
        data_path = self.archive_dir / str(year) / "data.json"
        if not data_path.is_file():
            return None
        try:
            return json.loads(data_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def archive_status(
        self,
        year: int | None = None,
        dataset_key: tuple[str, str, str] | None = None,
    ) -> dict[str, Any]:
        archive_year = year or self.current_year()
        archive = self._read_archive(archive_year)
        if dataset_key:
            slug = self._dataset_slug(*dataset_key)
            dataset_exists = bool(archive and any(
                dataset.get("slug") == slug
                for dataset in archive.get("datasets", [])
            ))
            return {
                "year": archive_year,
                "exists": dataset_exists,
                "archive_exists": archive is not None,
                "dataset": {
                    "sport": dataset_key[0],
                    "gender": dataset_key[1],
                    "level": dataset_key[2],
                    "slug": slug,
                    "label": self._dataset_label(*dataset_key),
                },
            }
        return {
            "year": archive_year,
            "exists": archive is not None,
            "complete": bool(
                archive and archive.get("complete", True)
            ),
        }

    def list_archives(self) -> dict[str, list[dict[str, Any]]]:
        if not self.archive_dir.is_dir():
            return {"archives": []}

        archives = []
        for path in self.archive_dir.iterdir():
            if not path.is_dir() or not path.name.isdigit():
                continue
            archive = self._read_archive(int(path.name))
            if archive:
                archives.append(self._archive_summary(archive))
        archives.sort(key=lambda item: item["year"], reverse=True)
        return {"archives": archives}

    def get_archive(self, year: int) -> dict[str, Any]:
        archive = self._read_archive(year)
        if archive is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Archive for {year} was not found",
            )
        return archive

    def _refresh_catalog(self):
        catalog = self.list_archives()
        temporary_path = self.archive_dir / ".index.json.tmp"
        self._write_json(temporary_path, catalog)
        temporary_path.replace(self.archive_dir / "index.json")

    def _write_archive(self, archive: dict[str, Any], target: Path):
        archive_year = archive["year"]
        self.archive_dir.mkdir(parents=True, exist_ok=True)
        temporary = Path(tempfile.mkdtemp(
            prefix=f".{archive_year}-",
            dir=self.archive_dir,
        ))
        backup = self.archive_dir / f".{archive_year}.backup"
        try:
            self._write_json(temporary / "data.json", archive)
            (temporary / "index.html").write_text(
                self._render_year_index(archive),
                encoding="utf-8",
            )
            for dataset in archive["datasets"]:
                (temporary / f"{dataset['slug']}.html").write_text(
                    self._render_dataset_page(
                        archive_year,
                        dataset.get("archived_at", archive["archived_at"]),
                        dataset,
                    ),
                    encoding="utf-8",
                )

            if backup.exists():
                shutil.rmtree(backup)
            if target.exists():
                target.replace(backup)
            temporary.replace(target)
            if backup.exists():
                shutil.rmtree(backup)
            self._refresh_catalog()
        except Exception:
            if temporary.exists():
                shutil.rmtree(temporary)
            if backup.exists() and not target.exists():
                backup.replace(target)
            raise

    async def archive_current_season(
        self,
        year: int | None = None,
        overwrite: bool = False,
        dataset_key: tuple[str, str, str] | None = None,
    ) -> dict[str, Any]:
        archive_year = year or self.current_year()
        target = self.archive_dir / str(archive_year)
        target_existed = target.exists()
        existing_archive = self._read_archive(archive_year)
        archive_exists = existing_archive is not None
        if dataset_key:
            dataset_key = tuple(str(value).lower() for value in dataset_key)
            selected_slug = self._dataset_slug(*dataset_key)
            dataset_existed = bool(existing_archive and any(
                dataset.get("slug") == selected_slug
                for dataset in existing_archive.get("datasets", [])
            ))
            if dataset_existed and not overwrite:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"{self._dataset_label(*dataset_key)} is already "
                        f"archived for {archive_year}"
                    ),
                )
            if target.exists() and not archive_exists and not overwrite:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=(
                        f"Archive for {archive_year} exists but could not be read"
                    ),
                )
        else:
            dataset_existed = False
        if not dataset_key and target.exists() and not overwrite:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Archive for {archive_year} already exists",
            )

        datasets = await self._current_datasets(archive_year, dataset_key)
        if not datasets:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=(
                    "The selected sport dataset is not available to archive"
                    if dataset_key
                    else "No sport datasets are available to archive"
                ),
            )

        archived_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        for dataset in datasets:
            dataset["archived_at"] = archived_at
        if dataset_key and existing_archive:
            retained_datasets = [
                dataset
                for dataset in existing_archive.get("datasets", [])
                if dataset.get("slug") != selected_slug
            ]
            for dataset in retained_datasets:
                dataset.setdefault(
                    "archived_at",
                    existing_archive.get("archived_at", archived_at),
                )
            datasets = [*retained_datasets, *datasets]
            datasets.sort(key=self._dataset_sort_key)

        archive = {
            "version": 2,
            "year": archive_year,
            "archived_at": archived_at,
            "dataset_count": len(datasets),
            "team_count": sum(dataset["team_count"] for dataset in datasets),
            "complete": (
                bool(existing_archive.get("complete", True))
                if dataset_key and existing_archive
                else not dataset_key
            ),
            "datasets": datasets,
        }
        self._write_archive(archive, target)

        summary = self._archive_summary(archive)
        if dataset_key:
            label = self._dataset_label(*dataset_key)
            message = f"Archived {archive_year} {label} rankings"
        else:
            message = f"Archived all sports for {archive_year}"
        return {
            **summary,
            "scope": "selected" if dataset_key else "all",
            "overwritten": dataset_existed if dataset_key else target_existed,
            "message": message,
        }
