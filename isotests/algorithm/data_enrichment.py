def enrich_data(df, k_value, average_game_score, home_advantage, teams):
    """
    Enrich data with calculated fields and recent opponent updates.
    """
    # Normalize team names in the DataFrame
    df['home_team'] = df['home_team'].str.strip().str.upper()
    df['away_team'] = df['away_team'].str.strip().str.upper()

    # Normalize team names in the dictionary
    teams = {key.strip().upper(): value for key, value in teams.items()}

    # Add constants
    df['k_value'] = k_value
    df['AVEGAMESC'] = average_game_score

    # Adjust home field advantage
    df['home_field_advantage'] = df['neutral_site'].apply(
        lambda x: 0 if x == 1 else home_advantage)

    # Map team data and handle missing teams
    def get_team_value(team, key, default):
        return teams[team][key] if team in teams else default

    df['home_team_power_ranking'] = df['home_team'].map(
        lambda x: get_team_value(x, 'power_ranking', 50))  # Default power_ranking: 50
    df['away_team_power_ranking'] = df['away_team'].map(
        lambda x: get_team_value(x, 'power_ranking', 50))  # Default power_ranking: 50
    df['home_team_win_ratio'] = df['home_team'].map(
        lambda x: get_team_value(x, 'win_ratio', 0.5))  # Default win_ratio: 0.5
    df['away_team_win_ratio'] = df['away_team'].map(
        lambda x: get_team_value(x, 'win_ratio', 0.5))  # Default win_ratio: 0.5

    # Update recent opponents
    for _, row in df.iterrows():
        home_team = row['home_team']
        away_team = row['away_team']

        if home_team not in teams:
            teams[home_team] = {"power_ranking": 50,
                                "win_ratio": 0.5, "recent_opp": []}
        if away_team not in teams:
            teams[away_team] = {"power_ranking": 50,
                                "win_ratio": 0.5, "recent_opp": []}

        teams[home_team]['recent_opp'].append(away_team)
        teams[away_team]['recent_opp'].append(home_team)

        # Keep recent opponents within a limit
        teams[home_team]['recent_opp'] = teams[home_team]['recent_opp'][-5:]
        teams[away_team]['recent_opp'] = teams[away_team]['recent_opp'][-5:]

    return df, teams
