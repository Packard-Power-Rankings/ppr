from utils import load_game_data_from_csv, calculate_performance, calculate_ranking, save_to_json, save_to_csv


def run_algorithm(games_csv, output_format='json'):
    # Load the data
    games_data = load_game_data_from_csv(games_csv)

    # Step 1: Extract unique teams from the games data
    teams = pd.DataFrame({'Team_Name': pd.concat(
        [games_data['Home_Team'], games_data['Visitor_Team']]).unique()})

    # Step 2: Calculate performance for each team
    performance_data = calculate_performance(teams, games_data)

    # Step 3: Calculate rankings based on performance
    ranking_data = calculate_ranking(performance_data)

    # Output the result in the desired format
    if output_format == 'json':
        save_to_json(ranking_data.to_dict(orient='records'), 'output.json')
        print("Output saved to 'output.json'")
    else:
        save_to_csv(ranking_data, 'output.csv')
        print("Output saved to 'output.csv'")


if __name__ == "__main__":
    games_csv = 'CFootballEx.csv'      # Update with actual file path
    output_format = 'json'               # Can be 'json' or 'csv'

    run_algorithm(games_csv, output_format)
