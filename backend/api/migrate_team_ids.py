"""Command-line entry point for the controlled team ID migration."""

import argparse
import asyncio
import json

from api.database import close_mongo_client
from api.service.team_id_migration import migrate_legacy_team_ids


async def run(apply: bool) -> None:
    summary = await migrate_legacy_team_ids(apply=apply)
    print(json.dumps(summary, indent=2, sort_keys=True))


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Migrate legacy teams.team_num values into canonical team_id values."
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Apply the migration. Without this option only a dry run is performed.",
    )
    args = parser.parse_args()
    try:
        asyncio.run(run(args.apply))
    finally:
        close_mongo_client()


if __name__ == "__main__":
    main()
