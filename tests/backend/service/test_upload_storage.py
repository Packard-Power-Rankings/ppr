from pathlib import Path

import pytest

from api.service.upload_storage import (
    delete_game_file,
    safe_filename,
    store_game_file,
)


def test_store_game_file_sanitizes_name_and_keeps_file_under_root(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))

    upload_id, storage_path = store_game_file(
        ("basketball", "mens", "high_school"),
        "../../Week 1 games.csv",
        b"game-data",
        upload_id="known-id",
    )

    assert upload_id == "known-id"
    assert storage_path == (
        "basketball/mens/high_school/known-id-Week-1-games.csv"
    )
    assert (tmp_path / storage_path).read_bytes() == b"game-data"
    assert safe_filename("../../Week 1 games.csv") == "Week-1-games.csv"


def test_delete_game_file_rejects_paths_outside_upload_root(
    monkeypatch,
    tmp_path,
):
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path / "uploads"))
    outside = tmp_path / "outside.csv"
    outside.write_text("keep")

    with pytest.raises(ValueError, match="outside the upload directory"):
        delete_game_file(str(Path("..") / "outside.csv"))

    assert outside.read_text() == "keep"
