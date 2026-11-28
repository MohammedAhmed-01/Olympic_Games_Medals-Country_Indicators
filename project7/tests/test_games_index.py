"""Tests for games index contract."""

import pandas as pd
import src.games_index as games_index


def test_games_index_contract(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(games_index, "PROJECT_ROOT", tmp_path)
    frame = games_index.build_games_index(download_status=False)
    expected = ["games_year", "held_year", "games_name", "url", "status", "include_in_scope", "notes"]
    assert list(frame.columns) == expected
    assert frame["games_year"].is_unique
    assert (frame.loc[frame["status"] == "cancelled", "include_in_scope"] == False).all()
    tokyo = frame.loc[frame["games_year"] == 2020].iloc[0]
    assert tokyo["held_year"] == 2021
