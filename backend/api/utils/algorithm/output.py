from pymongo import UpdateOne


async def update_teams(df, teams_data, mongo_collection, team_level):
    teams_names_dict = {
        team_name["team_name"].lower(): team_name for team_name in teams_data
    }

    # Need bulk update as well as need to update just power rankings
    # and recent opponent arrays

    for _, row in df.iterrows():
        home_team = teams_names_dict[row['home_team'].lower()]
        away_team = teams_names_dict[row['away_team'].lower()]
        game_id = f"{row['home_team']}_{row['away_team']}_{row['date']}"

        game_home_exists = await mongo_collection.find_one(
            {
                "_id": team_level.get("_id"),
                "teams": {
                    "$elemMatch": {
                        "team_id": home_team['team_id'],
                        "season_opp.game_id": game_id
                    }
                }
            }
        )
        game_away_exists = await mongo_collection.find_one(
            {
                "_id": team_level.get("_id"),
                "teams": {
                    "$elemMatch": {
                        "team_id": away_team['team_id'],
                        "season_opp.game_id": game_id
                    }
                }
            }
        )

        if game_home_exists and game_away_exists:
            update_home_data = {
                "$set": {
                    "teams.$[team].recent_opp": home_team['recent_opp']
                }
            }

            update_away_data = {
                "$set": {
                    "teams.$[team].recent_opp": away_team['recent_opp']
                }
            }

            await mongo_collection.update_one(
                {"_id": team_level.get("_id")},
                update_home_data,
                array_filters=[{"team.team_id": home_team['team_id']}]
            )

            await mongo_collection.update_one(
                {"_id": team_level.get("_id")},
                update_away_data,
                array_filters=[{"team.team_id": away_team['team_id']}]
            )
            continue

        home_win, home_loss = 0, 0
        away_win, away_loss = 0, 0

        if row['home_score'] > row['away_score']:
            home_win += 1
            away_loss += 1
        else:
            home_loss += 1
            away_win += 1

        season_home_opp = {
            "opponent_id": away_team.get("team_id"),
            "opponent_name": away_team.get("team_name"),
            "home_score": row['home_score'],
            "away_score": row['away_score'],
            "home_z_score": row['home_z_score'],
            "away_z_score": row['away_z_score'],
            "game_date": row['date'],
            "game_id": game_id
        }
        update_home_data = {
            "$set": {
                "teams.$[team].recent_opp": home_team['recent_opp']
            },
            "$inc": {
                "teams.$[team].wins": home_win,
                "teams.$[team].losses": home_loss
            },
            "$push": {
                "teams.$[team].season_opp": {
                    "$each": [season_home_opp],
                    "$position": 0
                }
            }
        }

        season_away_opp = {
            "opponent_id": home_team.get("team_id"),
            "opponent_name": home_team.get("team_name"),
            "home_score": row['home_score'],
            "away_score": row['away_score'],
            "home_z_score": row['home_z_score'],
            "away_z_score": row['away_z_score'],
            "game_date": row['date'],
            "game_id": game_id
        }
        update_away_data = {
            "$set": {

                "teams.$[team].recent_opp": away_team['recent_opp']
            },
            "$inc": {
                "teams.$[team].wins": away_win,
                "teams.$[team].losses": away_loss
            },
            "$push": {
                "teams.$[team].season_opp": {
                    "$each": [season_away_opp],
                    "$position": 0
                }
            }
        }

        await mongo_collection.update_one(
            {"_id": team_level.get("_id")},
            update_home_data,
            array_filters=[{"team.team_id": home_team['team_id']}]
        )

        await mongo_collection.update_one(
            {"_id": team_level.get("_id")},
            update_away_data,
            array_filters=[{"team.team_id": away_team['team_id']}]
        )
    bulk_operation = []
    for teams in teams_data:
        bulk_operation.append(
            UpdateOne(
                {"_id": team_level.get("_id"), "teams.team_id": teams["team_id"]},
                {"$set": {"teams.$.power_ranking": teams['power_ranking']}}
            )
        )
    mongo_collection.bulk_write(bulk_operation)
