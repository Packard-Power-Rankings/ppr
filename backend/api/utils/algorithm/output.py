from pymongo import UpdateOne


async def update_teams(df, teams_data, mongo_collection, team_level, date):
    teams_names_dict = {
        team_name["team_name"].lower(): team_name for team_name in teams_data
    }

    for _, row in df.iterrows():
        home_team = teams_names_dict[row['home_team'].lower()]
        away_team = teams_names_dict[row['away_team'].lower()]
        game_id = \
            f"{teams_names_dict[row['home_team'].lower()]['team_id']}_{teams_names_dict[row['away_team'].lower()]['team_id']}_{row['date']}"

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
            "home_team": 1,
            "home_score": row['home_score'],
            "away_score": row['away_score'],
            "home_z_score": 0.0,
            "away_z_score": 0.0,
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
                    "$position": -1
                }
            }
        }

        season_away_opp = {
            "opponent_id": home_team.get("team_id"),
            "opponent_name": home_team.get("team_name"),
            "home_team": 0,
            "home_score": row['home_score'],
            "away_score": row['away_score'],
            "home_z_score": 0.0,
            "away_z_score": 0.0,
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
                    "$position": -1
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
        new_pr = teams['power_ranking'][-1]
        bulk_operation.append(
            UpdateOne(
                {
                    "_id": team_level["_id"],
                    "teams.team_id": teams["team_id"],
                    "teams": {
                        "$not": {
                            "$elemMatch": {
                                "team_id": teams["team_id"],
                                "power_ranking": {
                                    "$elemMatch": {
                                        "$and": [
                                            {date: {"$exists": True}}
                                        ]
                                    }
                                }
                            }
                        }
                    }
                },
                {
                    "$push": {
                        "teams.$.power_ranking": {date: new_pr}
                    }
                }
            )
        )

        bulk_operation.append(
            UpdateOne(
                {
                    "_id": team_level["_id"],
                    "teams.team_id": teams["team_id"],
                    "teams": {
                        "$elemMatch": {
                            "team_id": teams["team_id"],
                            "power_ranking": {
                                "$elemMatch": {
                                    date: {"$exists": True}
                                }
                            }
                        }
                    }
                },
                {
                    "$set": {
                        f"teams.$[team].power_ranking.$[entry].{date}": new_pr
                    }
                },
                array_filters=[
                    {"team.team_id": teams["team_id"]},
                    {f"entry.{date}": {"$exists": True}}
                ]
            )
        )
    await mongo_collection.bulk_write(bulk_operation)


async def set_z_scores(df, teams_data, mongo_collection, team_level):
    teams_names_dict = {
        team_name["team_name"].lower(): team_name for team_name in teams_data
    }

    bulk_operation = []
    for _, row in df.iterrows():

        home_team = teams_names_dict[row['home_team'].lower()]
        away_team = teams_names_dict[row['away_team'].lower()]
        game_id = f"{row['home_team']}_{row['away_team']}_{row['date']}"

        bulk_operation.append(
            UpdateOne(
                {
                    "_id": team_level['_id'],
                    "teams.team_id": home_team['team_id'],
                    "teams.season_opp.game_id": game_id
                },
                {
                    "$set": {
                        "teams.$[team].season_opp.$[game].home_z_score":
                        row['home_z_score'],
                        "teams.$[team].season_opp.$[game].away_z_score":
                        row['away_z_score']
                    }
                },
                array_filters=[
                    {"team.team_id": home_team['team_id']},
                    {"game.game_id": game_id}
                ]
            )
        )

        bulk_operation.append(
            UpdateOne(
                {
                    "_id": team_level['_id'],
                    "teams.team_id": away_team['team_id'],
                    "teams.season_opp.game_id": game_id
                },
                {
                    "$set": {
                        "teams.$[team].season_opp.$[game].home_z_score":
                        row['home_z_score'],
                        "teams.$[team].season_opp.$[game].away_z_score":
                        row['away_z_score']
                    }
                },
                array_filters=[
                    {"team.team_id": away_team['team_id']},
                    {"game.game_id": game_id}
                ]
            )
        )
    await mongo_collection.bulk_write(bulk_operation)
