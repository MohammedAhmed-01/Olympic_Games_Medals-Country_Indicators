"""Tests for World Bank parsing and offline behavior."""

import pandas as pd
import src.ingest_worldbank as ingest
import src.pipeline as pipeline

from src.ingest_worldbank import _process_csv


def test_skiprows_and_numeric_year_columns(tmp_path) -> None:
    fixture = tmp_path / "worldbank.csv"
    fixture.write_text(
        "metadata line\nmetadata line\nmetadata line\nmetadata line\n"
        "Country Name,Country Code,Indicator Name,Indicator Code,1960,2024,Unnamed: 6\n"
        "Aland,ALA,Population,total,10,20,\n",
        encoding="utf-8",
    )
    frame = _process_csv(fixture, "test_output.csv", 4, None)
    assert "Unnamed: 6" not in frame.columns
    assert pd.api.types.is_numeric_dtype(frame["1960"])
    assert pd.api.types.is_numeric_dtype(frame["2024"])


def test_offline_stage_makes_zero_network_calls(monkeypatch) -> None:
    from unittest.mock import Mock

    network_request = Mock()
    monkeypatch.setattr(ingest.requests, "get", network_request)
    monkeypatch.setattr("sys.argv", ["src.pipeline", "--offline", "--stage", "ingest"])
    assert pipeline.main() == 0
    network_request.assert_not_called()
