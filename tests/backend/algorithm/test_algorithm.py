# import pytest
# import pandas as pd
# from hypothesis import given, strategies as st, assume
# from math import isnan
# from main import (
#     calculate_z_scores,
#     calculate_expected_performance,
#     calculate_actual_performance,
#     power_change,
#     modify_game_scores,
#     calculate_power_difference,
# )

# # --- Tests for Basic Calculations ---


# def test_calculate_z_scores():
#     df = pd.DataFrame({
#         'home_score': [100, 80, 90],
#         'away_score': [85, 95, 100]
#     })
#     result_df = calculate_z_scores(df, 6)
#     assert 'home_z_score' in result_df.columns
#     assert 'away_z_score' in result_df.columns
#     assert result_df['home_z_score'].notnull().all()
#     assert result_df['away_z_score'].notnull().all()


# @given(expected=st.floats(min_value=-100, max_value=100, allow_nan=False))
# def test_calculate_expected_performance(expected):
#     result = calculate_expected_performance(expected)
#     if expected + 2.0 < 0:
#         assert isnan(result)  # Ensure invalid inputs return NaN
#     else:
#         assert isinstance(result, float)  # Ensure valid inputs return a float


# def test_calculate_actual_performance():
#     assert calculate_actual_performance(10) == pytest.approx(2.693, 0.1)
#     assert calculate_actual_performance(-5) == pytest.approx(-2.1, 0.1)

# # --- Tests for Power Difference ---


# def test_power_change():
#     assert power_change(3, 2.5, 0.5) == pytest.approx(0.25, 0.01)
#     assert power_change(1, 1, 1) == 0


# def test_calculate_power_difference():
#     df = pd.DataFrame({
#         'home_team_power_ranking': [1500, 1500],
#         'away_team_power_ranking': [1400, 1600],
#         'expected_home_wl': [1, -1],
#         'expected_away_wl': [-1, 1],
#         'modified_home_score': [1, 0],
#         'modified_away_score': [0, 1],
#         'k_value': [30, 30],
#     })
#     result_df = calculate_power_difference(df)
#     assert 'home_team_power_ranking' in result_df.columns
#     assert 'away_team_power_ranking' in result_df.columns

# # --- Tests for Game Modifications ---


# @given(
#     home_scores=st.lists(st.integers(
#         min_value=0, max_value=200), min_size=1, max_size=50),
#     away_scores=st.lists(st.integers(
#         min_value=0, max_value=200), min_size=1, max_size=50),
#     ave_game_score=st.integers(min_value=1, max_value=200)
# )
# def test_modify_game_scores(home_scores, away_scores, ave_game_score):
#     assume(len(home_scores) == len(away_scores))  # Ensure equal lengths

#     df = pd.DataFrame({
#         'home_score': home_scores,
#         'away_score': away_scores,
#         'AVEGAMESC': [ave_game_score] * len(home_scores)
#     })

#     result_df = modify_game_scores(df)
#     assert 'modified_home_score' in result_df.columns
#     assert 'modified_away_score' in result_df.columns
#     assert result_df['modified_home_score'].notnull().all()
#     assert result_df['modified_away_score'].notnull().all()
