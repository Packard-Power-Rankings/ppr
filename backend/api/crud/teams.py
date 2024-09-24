import hashlib
from typing import List, Any, Dict
from bson.objectid import ObjectId
from api.utils.dependencies import get_database
from api.utils.json_helper import json_file_builder
from api.utils.update_algo_vals import update_values

db = get_database()
teams_collection = db.get_collection("sports")


async def create_sport(
        sport_type: str,
        gender: str,
        level: str,
        team_data: List[List],
        **algo_vals
):
    sport_doc = json_file_builder(
        sport_type=sport_type,
        gender=gender,
        level=level
    )

    if algo_vals:
        # Function to update algorithm values if need be otherwise
        # they stay there constant value

        level_key = (sport_type, gender, level)
        sport_doc = update_values(
            level_key=level_key,
            sport_json_doc=sport_doc,
            algo_vals=algo_vals
        )

    teams = sport_doc['sports'][sport_type][gender][level]['teams']

    for team in team_data:
        team_one, team_two, team_one_score, team_two_score = \
            team

        team_one_win = 0
        team_two_win = 0
        team_one_loss = 0
        team_two_loss = 0

        if team_one_score > team_two_score:
            team_one_win += 1
            team_two_loss += 1
        else:
            team_two_win += 1
            team_one_loss += 1

        # Main algorithm call with team 1 and team 2 scores for
        # calculations of z_score and power rankings. Then storing
        # them into the db

        dummy_z_score_1 = 0.0
        dummy_z_score_2 = 0.0
        dummy_pr_val_1 = 0.0
        dummy_pr_val_2 = 0.0

        # Values above are just temp as if they were used for a
        # function call to get a return value.

        dummy_division = ""
        dummy_conference = ""

        team_one_id: str = hashlib.sha256(
            team_one,
            usedforsecurity=False).hexdigest()
        team_two_id: str = hashlib.sha256(
            team_two,
            usedforsecurity=False).hexdigest()

        for \
            team_id, team_name, conf, division, wins, \
            loss, z_score, pr_val, opp_id, team_score \
            in [
                (
                    team_one_id, team_one, dummy_conference,
                    dummy_division, team_one_win, team_one_loss,
                    dummy_z_score_1, dummy_pr_val_1, team_two_id,
                    team_one_score
                ),
                (
                    team_two_id, team_two, dummy_conference,
                    dummy_division, team_two_win, team_two_loss,
                    dummy_z_score_2, dummy_pr_val_2, team_one_id,
                    team_two_score,
                )
                ]:
            team_info = {
                team_id: {
                    "team_name": team_name,
                    "city": "",
                    "state": "",
                    "conference": conf,
                    "division": division,
                    "wins": wins,
                    "losses": loss,
                    "z_score": z_score,
                    "power_ranking": pr_val,
                    "season_opp": [
                        {
                            "opp_id": opp_id,
                            "match_score": team_score,
                            "date": ""
                        }
                    ]
                }
            }
            teams.append(team_info)

    sport_doc['sports'][sport_type][gender][level]['teams'] = teams

    query = {
        f"sports.{sport_type}.{gender}.{level}": {"$exists": True}
    }

    result = await teams_collection.updateMany(
        query,
        {"$set": sport_doc},
        upsert=True
    )

    return result
