import pandas as pd
import json

# Data Loading Functions


def load_game_data_from_csv(file_path):
    """Loads game data from a CSV file."""
    return pd.read_csv(file_path)

# Core Algorithm Functions


def calculate_performance(team_data, games_data):
    """Calculates performance metrics for each team."""

    performance_data = []

    for _, team in team_data.iterrows():
        team_name = team['Team_Name']

        # Filter games where the team participated
        team_games = games_data[
            (games_data['Home_Team'] == team_name) |
            (games_data['Visitor_Team'] == team_name)
        ]

        # Initialize metrics
        wins = 0
        losses = 0
        points_for = 0
        points_against = 0

        for _, game in team_games.iterrows():
            if game['Home_Team'] == team_name:
                points_for += game['Home_Team_Score']
                points_against += game['Visitor_Team_Score']
                if game['Home_Team_Score'] > game['Visitor_Team_Score']:
                    wins += 1
                else:
                    losses += 1
            elif game['Visitor_Team'] == team_name:
                points_for += game['Visitor_Team_Score']
                points_against += game['Home_Team_Score']
                if game['Visitor_Team_Score'] > game['Home_Team_Score']:
                    wins += 1
                else:
                    losses += 1

        # Calculate point differential
        point_differential = points_for - points_against

        # Append performance metrics for this team
        performance_data.append({
            "team_name": team_name,
            "wins": wins,
            "losses": losses,
            "points_for": points_for,
            "points_against": points_against,
            "point_differential": point_differential
        })

    return pd.DataFrame(performance_data)


def calculate_ranking(performance_data):
    """Calculates team rankings based on performance data."""

    # Sort by wins and then point differential
    ranking = performance_data.sort_values(
        by=["wins", "point_differential"], ascending=[False, False])
    ranking['rank'] = range(1, len(ranking) + 1)

    return ranking

# Output Handling Functions


def save_to_json(data, output_file):
    """Saves the result to a JSON file."""
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=4)


def save_to_csv(data, output_file):
    """Saves the result to a CSV file."""
    data.to_csv(output_file, index=False)
