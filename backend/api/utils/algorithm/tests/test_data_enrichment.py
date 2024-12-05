import pytest
import pandas as pd
from data_enrichment import enrich_data


def test_enrich_data_valid_data():
    # Create a sample DataFrame and team data
    df = pd.DataFrame({
        'date': ['2023-11-19', '2023-11-20'],
        'home_team': ['Team A', 'Team B'],
        'away_team': ['Team C', 'Team D'],
        'home_score': [100, 95],
        'away_score': [90, 85],
        'neutral_site': [0, 999]
    })

    teams = [
        {"team_name": "Team A", "power_ranking": [1500], "win_ratio": 0.75},
        {"team_name": "Team B", "power_ranking": [1400], "win_ratio": 0.65},
        {"team_name": "Team C", "power_ranking": [1300], "win_ratio": 0.55},
        {"team_name": "Team D", "power_ranking": [1200], "win_ratio": 0.45}
    ]

    enriched_df = enrich_data(
        df, k_value=30, home_advantage=50, average_game_score=200, teams=teams)

    # Assert new columns are added
    assert 'k_value' in enriched_df.columns
    assert 'AVEGAMESC' in enriched_df.columns
    assert 'home_field_advantage' in enriched_df.columns
    assert 'home_team_power_ranking' in enriched_df.columns
    assert 'away_team_power_ranking' in enriched_df.columns

    # Assert values are correctly assigned
    assert enriched_df['k_value'].tolist() == [30, 30]
    assert enriched_df['AVEGAMESC'].tolist() == [200, 200]
    assert enriched_df['home_field_advantage'].tolist() == [
        50, 0]  # Neutral site handling
    assert enriched_df['home_team_power_ranking'].tolist() == [1500, 1400]
    assert enriched_df['away_team_power_ranking'].tolist() == [1300, 1200]


def test_enrich_data_unknown_team():
    # Create a DataFrame with a team not in the `teams` list
    df = pd.DataFrame({
        'date': ['2023-11-19'],
        'home_team': ['Team Z'],  # Unknown team
        'away_team': ['Team A'],
        'home_score': [100],
        'away_score': [90],
        'neutral_site': [0]
    })

    teams = [
        {"team_name": "Team A", "power_ranking": [1500], "win_ratio": 0.75}
    ]

    # Enrich data
    with pytest.raises(KeyError):
        enrich_data(df, k_value=30, home_advantage=50,
                    average_game_score=200, teams=teams)


def test_enrich_data_random_win_ratios():
    # Create a sample DataFrame and team data
    df = pd.DataFrame({
        'date': ['2023-11-19'],
        'home_team': ['Team A'],
        'away_team': ['Team B'],
        'home_score': [100],
        'away_score': [90],
        'neutral_site': [0]
    })

    teams = [
        {"team_name": "Team A", "power_ranking": [1500], "win_ratio": 0.75},
        {"team_name": "Team B", "power_ranking": [1400], "win_ratio": 0.65},
    ]

    enriched_df = enrich_data(
        df, k_value=30, home_advantage=50, average_game_score=200, teams=teams)

    # Assert win ratios are random within the specified range
    assert 0.3 <= enriched_df['home_team_win_ratio'].iloc[0] <= 0.9
    assert 0.3 <= enriched_df['away_team_win_ratio'].iloc[0] <= 0.9


def test_enrich_data_empty_dataframe():
    # Test with an empty DataFrame
    df = pd.DataFrame(columns=[
                      'date', 'home_team', 'away_team', 'home_score', 'away_score', 'neutral_site'])

    teams = [
        {"team_name": "Team A", "power_ranking": [1500], "win_ratio": 0.75},
    ]

    enriched_df = enrich_data(
        df, k_value=30, home_advantage=50, average_game_score=200, teams=teams)

    # Assert the resulting DataFrame is still empty but has new columns
    assert enriched_df.empty
    assert 'k_value' in enriched_df.columns
    assert 'AVEGAMESC' in enriched_df.columns
    assert 'home_field_advantage' in enriched_df.columns
    assert 'home_team_power_ranking' in enriched_df.columns
    assert 'away_team_power_ranking' in enriched_df.columns
