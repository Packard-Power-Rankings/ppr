from api.service.admin_teams import AdminTeamsService


def test_remove_team_removes_reciprocal_games_and_repairs_records():
    teams = [
        {
            "team_id": 1,
            "team_name": "Delete Me",
            "wins": 1,
            "losses": 1,
            "recent_opp": [2, 3, 0, 0, 0],
            "season_opp": [
                {"game_id": "game-1", "opponent_id": 2},
                {"game_id": "game-2", "opponent_id": 3},
            ],
        },
        {
            "team_id": 2,
            "team_name": "Opponent One",
            "wins": 4,
            "losses": 2,
            "recent_opp": [1, 8, 0, 0, 0],
            "season_opp": [
                {
                    "game_id": "game-1",
                    "opponent_id": 1,
                    "opponent_name": "Delete Me",
                    "home_team": 0,
                    "home_score": 80,
                    "away_score": 70,
                },
                {
                    "game_id": "unrelated",
                    "opponent_id": 8,
                    "home_team": 1,
                    "home_score": 75,
                    "away_score": 60,
                },
            ],
        },
        {
            "team_id": 3,
            "team_name": "Opponent Two",
            "wins": 3,
            "losses": 3,
            "recent_opp": [1, 0, 0, 0, 0],
            "season_opp": [
                {
                    "game_id": "game-2",
                    "opponent_id": 1,
                    "opponent_name": "Delete Me",
                    "home_team": 1,
                    "home_score": 90,
                    "away_score": 80,
                }
            ],
        },
    ]

    remaining_teams, stats = AdminTeamsService._remove_team_from_teams(
        teams,
        1,
        "Delete Me"
    )

    assert [team["team_id"] for team in remaining_teams] == [2, 3]
    assert stats == {
        "team_found": True,
        "team_games_removed": 2,
        "linked_games_removed": 2,
    }
    assert remaining_teams[0]["losses"] == 1
    assert remaining_teams[0]["wins"] == 4
    assert [game["game_id"] for game in remaining_teams[0]["season_opp"]] == [
        "unrelated"
    ]
    assert remaining_teams[0]["recent_opp"] == [0, 8, 0, 0, 0]
    assert remaining_teams[1]["wins"] == 2
    assert remaining_teams[1]["recent_opp"] == [0, 0, 0, 0, 0]


def test_remove_team_cleans_orphaned_game_references():
    teams = [
        {
            "team_id": 2,
            "team_name": "Opponent",
            "wins": 0,
            "losses": 1,
            "recent_opp": [99, 0, 0, 0, 0],
            "season_opp": [
                {
                    "game_id": "orphaned-game",
                    "opponent_id": 99,
                    "opponent_name": "Missing Team",
                    "home_team": 1,
                    "home_score": 10,
                    "away_score": 20,
                }
            ],
        }
    ]

    remaining_teams, stats = AdminTeamsService._remove_team_from_teams(
        teams,
        99,
        "Missing Team"
    )

    assert stats["team_found"] is False
    assert stats["linked_games_removed"] == 1
    assert remaining_teams[0]["losses"] == 0
    assert remaining_teams[0]["season_opp"] == []
    assert remaining_teams[0]["recent_opp"] == [0, 0, 0, 0, 0]
