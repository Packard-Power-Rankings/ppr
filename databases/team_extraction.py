import sqlite3
import motor.motor_asyncio

MONGO_DETAILS = \
    f"mongodb+srv://{os.getenv("MONGO_USER")}:{os.getenv("MONGO_PASS")}@" \
    "sports-cluster.mx1mo.mongodb.net/" \
    "?retryWrites=true&w=majority&appName=Sports-Cluster"
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DETAILS)
database = client["sports_data"]
sports_collection = database.get_collection('teams_data')
# from basketball_w import C_WBB_TEAM_INFO

# team_dict = C_WBB_TEAM_INFO

# Doing College Football First

connection = sqlite3.connect(
    '/Users/danielfishbein/Documents/ppr/databases/db.sqlite3'
)
cursor = connection.cursor()

# query = """
#     SELECT t.name, t.team_num, t.division_id_id, t.state_id_id, t.conference_id_id, p.power, p.recent_opponent_1, p.recent_opponent_2, p.recent_opponent_3, p.recent_opponent_4, p.recent_opponent_5
#     FROM sport_information_team t
#     JOIN sport_information_teamweeklydata p
#     ON t.id = p.team_id_id
#     WHERE p.week_id_id = 205;
# """

query = """
        SELECT
        t.name,
        t.team_num,
        d.name AS division_name,
        s.name AS state_name,
        c.name AS conference_name,
        p.power,
        p.recent_opponent_1,
        p.recent_opponent_2,
        p.recent_opponent_3,
        p.recent_opponent_4,
        p.recent_opponent_5,
        p.overall_rank,
        p.div_rank
    FROM sport_information_team t
    JOIN sport_information_teamweeklydata p
        ON t.id = p.team_id_id
    JOIN general_information_division d
        ON t.division_id_id = d.id
    JOIN general_information_state s
        ON t.state_id_id = s.id
    JOIN general_information_conference c
        ON t.conference_id_id = c.id
    WHERE p.week_id_id = 205;
"""

cursor.execute(query)
rows = cursor.fetchall()

team_list = []

# home_team_data = {
#             "team_id": team_state.team_id(level_key, row['home_team']),
#             "team_name": row['home_team'],
#             "city": '',
#             "state": STATES[
#                 team_state.team_state_id(level_key, row['home_team'])
#             ],
#             "division": team_state.team_division(level_key, row['home_team']),
#             "conference": team_state.team_conference(
#                 level_key, row['home_team']
#             ),
#             "power_ranking": row['home_team_power_ranking'],
#             "win_ratio": row['home_team_win_ratio'],
#             "wins": home_win,
#             "losses": home_loss,
#             "date": game_date,
#             "season_opp": [
#                 {
#                     "opponent_id": team_state.team_id(
#                         level_key, row['away_team']),
#                     "home_team": True,
#                     "home_score": row['home_score'],
#                     "away_score": row['away_score'],
#                     "home_z_score": row['home_z_score'],
#                     "away_z_score": row['away_z_score'],
#                     "date": game_date
#                 }
#             ]
#         }

for row in rows:
    team_name, team_num, division, state, conference, pr, recent_opp_1, recent_opp_2, recent_opp_3, recent_opp_4, recent_opp_5, overall_rank, div_rank = row

    team_list.append(
        {
            "team_id": team_num,
            "team_name": team_name,
            "city": "",
            "state": state,
            "division": division,
            "conference": conference,
            "division_rank": div_rank,
            "overall_rank": overall_rank,
            "power_ranking": pr,
            "win_ratio": 0.0,
            "wins": 0,
            "losses": 0,
            "date": "",
            "recent_opp": [
                recent_opp_1,
                recent_opp_2,
                recent_opp_3,
                recent_opp_4,
                recent_opp_5
            ],
            "season_opp": []
        }
    )

connection.close()


