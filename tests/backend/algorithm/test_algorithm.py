import pandas as pd
import pytest

from api.utils.algorithm.main import calculate_z_scores


def test_z_scores_use_both_home_and_away_changes_for_scale():
    frame = pd.DataFrame({
        "home_score": [80, 65],
        "away_score": [70, 75],
        "AVEGAMESC": [106, 106],
        "home_team_power_ranking": [100.0, 95.0],
        "away_team_power_ranking": [90.0, 105.0],
        "home_field_advantage": [4.5, 4.5],
        "k_value": [0.43, 0.43],
    })

    result = calculate_z_scores(frame, 2 * len(frame.index))
    mean_squared_z = (
        result["home_z_score"].pow(2).sum()
        + result["away_z_score"].pow(2).sum()
    ) / (2 * len(result.index))

    assert mean_squared_z == pytest.approx(1.0)
