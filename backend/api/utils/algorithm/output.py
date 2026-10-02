"""Persistence of derived ranking and z-score data."""

from collections import defaultdict

from pymongo import UpdateOne

from api.service.game_ingestion import canonical_game_id


def _number(value) -> float:
    return float(value)


async def update_teams(df, teams_data, mongo_collection, team_level, date):
    """Replace all derived season data from one deterministic calculation."""
    teams_by_name = {
        team["team_name"].casefold(): team for team in teams_data
    }
    season_games = defaultdict(list)
    records = {
        team["team_id"]: {"wins": 0, "losses": 0}
        for team in teams_data
    }

    for _, row in df.iterrows():
        home_team = teams_by_name[row["home_team"].casefold()]
        away_team = teams_by_name[row["away_team"].casefold()]
        game_id = canonical_game_id(
            row["date"],
            home_team["team_id"],
            away_team["team_id"],
        )
        home_won = row["home_score"] > row["away_score"]
        records[home_team["team_id"]]["wins" if home_won else "losses"] += 1
        records[away_team["team_id"]]["losses" if home_won else "wins"] += 1
        common = {
            "home_score": int(row["home_score"]),
            "away_score": int(row["away_score"]),
            "home_z_score": _number(row.get("home_z_score", 0.0)),
            "away_z_score": _number(row.get("away_z_score", 0.0)),
            "game_date": row["date"],
            "game_id": game_id,
        }
        season_games[home_team["team_id"]].append({
            **common,
            "opponent_id": away_team["team_id"],
            "opponent_name": away_team["team_name"],
            "home_team": 1,
        })
        season_games[away_team["team_id"]].append({
            **common,
            "opponent_id": home_team["team_id"],
            "opponent_name": home_team["team_name"],
            "home_team": 0,
        })

    ordered_teams = sorted(
        teams_data,
        key=lambda team: (
            -_number(team["power_ranking"][-1]),
            team["team_name"].casefold(),
        ),
    )
    overall_ranks = {
        team["team_id"]: rank
        for rank, team in enumerate(ordered_teams, start=1)
    }
    last_ranks = {
        team["team_id"]: team.get("overall_rank") or 0
        for team in teams_data
    }
    division_ranks = {}
    conference_ranks = {}
    divisions = defaultdict(list)
    conferences = defaultdict(list)
    for team in ordered_teams:
        divisions[team.get("division")].append(team)
        conferences[team.get("conference")].append(team)
    for division_teams in divisions.values():
        for rank, team in enumerate(division_teams, start=1):
            division_ranks[team["team_id"]] = rank
    for conference_teams in conferences.values():
        for rank, team in enumerate(conference_teams, start=1):
            conference_ranks[team["team_id"]] = rank

    operations = []
    for team in teams_data:
        team_id = team["team_id"]
        record = records[team_id]
        games_played = record["wins"] + record["losses"]
        initial = _number(team.get("initial_power_ranking", 0.0))
        final = _number(team["power_ranking"][-1])
        power_history = [{"initial": initial}]
        if date:
            power_history.append({date: final})
        operations.append(UpdateOne(
            {"_id": team_level["_id"], "teams.team_id": team_id},
            {"$set": {
                "teams.$.wins": record["wins"],
                "teams.$.losses": record["losses"],
                "teams.$.win_ratio": (
                    record["wins"] / games_played if games_played else 0.0
                ),
                "teams.$.recent_opp": list(team["recent_opp"]),
                "teams.$.season_opp": season_games[team_id],
                "teams.$.power_ranking": power_history,
                "teams.$.overall_rank": overall_ranks[team_id],
                "teams.$.last_rank": last_ranks[team_id],
                "teams.$.division_rank": division_ranks[team_id],
                "teams.$.conference_rank": conference_ranks[team_id],
                "teams.$.date": date,
            }},
        ))
    if operations:
        await mongo_collection.bulk_write(operations, ordered=False)
        await mongo_collection.update_one(
            {"_id": team_level["_id"]},
            {"$set": {"rankings_stale": False}},
        )


async def set_z_scores(
    df,
    teams_data,
    mongo_collection,
    games_collection,
    team_level,
    level_key,
):
    """Persist z-scores to canonical games and both team-facing records."""
    teams_by_name = {
        team["team_name"].casefold(): team for team in teams_data
    }
    team_operations = []
    game_operations = []
    for _, row in df.iterrows():
        home_team = teams_by_name[row["home_team"].casefold()]
        away_team = teams_by_name[row["away_team"].casefold()]
        game_id = canonical_game_id(
            row["date"],
            home_team["team_id"],
            away_team["team_id"],
        )
        home_z_score = _number(row["home_z_score"])
        away_z_score = _number(row["away_z_score"])
        game_operations.append(UpdateOne(
            {
                "sport_type": level_key[0],
                "gender": level_key[1],
                "level": level_key[2],
                "game_id": game_id,
            },
            {"$set": {
                "home_z_score": home_z_score,
                "away_z_score": away_z_score,
            }},
        ))
        for team in (home_team, away_team):
            team_operations.append(UpdateOne(
                {
                    "_id": team_level["_id"],
                    "teams": {"$elemMatch": {
                        "team_id": team["team_id"],
                        "season_opp.game_id": game_id,
                    }},
                },
                {"$set": {
                    "teams.$[team].season_opp.$[game].home_z_score": home_z_score,
                    "teams.$[team].season_opp.$[game].away_z_score": away_z_score,
                }},
                array_filters=[
                    {"team.team_id": team["team_id"]},
                    {"game.game_id": game_id},
                ],
            ))
    if game_operations:
        await games_collection.bulk_write(game_operations, ordered=False)
    if team_operations:
        await mongo_collection.bulk_write(team_operations, ordered=False)
