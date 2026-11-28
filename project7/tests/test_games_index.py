"""Tests for games index contract."""

import pandas as pd

from src.games_index import build_games_index


def test_games_index_contract() -> None:
    frame = build_games_index(download_status=False)
    expected = ["games_year", "held_year", "games_name", "url", "status", "include_in_scope", "notes"]
    assert list(frame.columns) == expected
    assert frame["games_year"].is_unique
    assert (frame.loc[frame["status"] == "cancelled", "include_in_scope"] == False).all()
    tokyo = frame.loc[frame["games_year"] == 2020].iloc[0]
    assert tokyo["held_year"] == 2021
