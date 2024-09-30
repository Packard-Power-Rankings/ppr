import json


def output_to_json(df, output_file_path):
    """
    Converts the final DataFrame to JSON format and saves it to a file.
    Reformats the output so that each team has its own section.
    :param df: DataFrame containing the final processed data.
    :param output_file_path: The file path where the JSON will be saved.
    :return: None
    """
    # List to hold the formatted data
    output_data = []

    # Loop through each row (game) in the DataFrame
    for _, row in df.iterrows():
        # Extract only the date part (no time) and convert to string
        game_date = row['date'].date().isoformat()

        # Create a section for the home team
        home_team_data = {
            "team": row['home_team'],
            "date": game_date,
            "home_team": True,
            "opponent": row['away_team'],
            "team_score": row['home_score'],
            "opponent_score": row['away_score'],
            "power_ranking": row['home_team_power_ranking'],
            "win_ratio": row['home_team_win_ratio'],
            "power_difference": row['power_difference'],
            "z_score": row['home_z_score'],
            "expected_performance": row['expected_performance_home'],
            "actual_performance": row['actual_performance_home'],
            "predicted_score": row['predicted_home_score']
        }
        output_data.append(home_team_data)

        # Create a section for the away team
        away_team_data = {
            "team": row['away_team'],
            "date": game_date,
            "home_team": False,
            "opponent": row['home_team'],
            "team_score": row['away_score'],
            "opponent_score": row['home_score'],
            "power_ranking": row['away_team_power_ranking'],
            "win_ratio": row['away_team_win_ratio'],
            "power_difference": row['power_difference'],
            "z_score": row['away_z_score'],
            "expected_performance": row['expected_performance_away'],
            "actual_performance": row['actual_performance_away'],
            "predicted_score": row['predicted_away_score']
        }
        output_data.append(away_team_data)

    # Write the JSON data to a file
    with open(output_file_path, 'w') as json_file:
        json.dump(output_data, json_file, indent=4)

    print(f"Results saved to {output_file_path}")
