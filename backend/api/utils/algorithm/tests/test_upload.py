import pytest
import pandas as pd
from io import StringIO
from upload import upload_csv


def test_upload_csv_valid_file():
    # Mock a valid CSV file using StringIO
    csv_data = StringIO(
        "2023-11-19,Team A,Team B,100,90,0\n"
        "2023-11-20,Team C,Team D,95,85,999\n"
    )
    df = upload_csv(csv_data)

    assert isinstance(df, pd.DataFrame)
    assert list(df.columns) == [
        "date", "home_team", "away_team", "home_score", "away_score", "neutral_site"]
    assert len(df) == 2  # Two rows of data
    assert df.loc[0, "home_team"] == "Team A"
    assert df.loc[1, "neutral_site"] == 999


def test_upload_csv_missing_column():
    # Mock a CSV missing a required column
    csv_data = StringIO(
        "2023-11-19,Team A,100,90,0\n"
        "2023-11-20,Team C,95,85,999\n"
    )
    with pytest.raises(ValueError, match="CSV does not contain the correct number of columns."):
        upload_csv(csv_data)


def test_upload_csv_invalid_file():
    # Test with an invalid file path
    result = upload_csv("non_existent_file.csv")
    assert result is None


def test_upload_csv_empty_file():
    # Mock an empty CSV file
    csv_data = StringIO("")
    df = upload_csv(csv_data)
    assert df.empty
    assert list(df.columns) == [
        "date", "home_team", "away_team", "home_score", "away_score", "neutral_site"]
