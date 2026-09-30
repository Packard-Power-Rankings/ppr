from upload import upload_csv
from data_cleaning import clean_data
from data_enrichment import enrich_data
from main import run_calculations
from output import save_to_csv
from compare_outputs import compare_outputs


def run_pipeline(teams_file, game_files, output_files):
    """
    Execute the pipeline for the given teams and game files.
    """
    # Load initial team data
    teams_schema = ["team_name", "power_ranking", "win_ratio", "recent_opp"]
    teams_df = upload_csv(teams_file, schema=teams_schema)

    # Normalize team names when creating the dictionary
    teams = {
        str(row['team_name']).strip().upper(): {
            "power_ranking": row['power_ranking'],
            "win_ratio": row['win_ratio'],
            "recent_opp": row['recent_opp'].split(",") if isinstance(row['recent_opp'], str) else []
        }
        for _, row in teams_df.iterrows()
    }

    # Process each game file
    for i, game_file in enumerate(game_files):
        # Load and clean the game data
        games_df = upload_csv(game_file)
        games_df = clean_data(games_df)

        # Enrich and calculate
        games_df, teams = enrich_data(
            games_df,
            k_value=0.43,
            average_game_score=106,
            home_advantage=4.5,
            teams=teams
        )

        # Convert teams to the format expected by main.py
        teams_data = [
            {"team_id": key, "team_name": key, **value}
            for key, value in teams.items()
        ]

        # Run calculations
        games_df, teams_data = run_calculations(games_df, teams_data)

        # Convert back to the dictionary format
        teams = {team["team_name"]: {k: v for k, v in team.items(
        ) if k not in ["team_id", "team_name"]} for team in teams_data}

        # Save output
        save_to_csv(games_df, output_files[i])


if __name__ == "__main__":
    teams_path = "TEAMSNEW.csv"
    games_paths = ["GAMES1.csv", "GAMES2.csv", "GAMES3.csv"]
    output_paths = ["OUT1_generated.csv",
                    "OUT2_generated.csv", "OUT3_generated.csv"]

    run_pipeline(teams_path, games_paths, output_paths)
