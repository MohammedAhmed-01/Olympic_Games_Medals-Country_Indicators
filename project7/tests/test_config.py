"""Tests for configuration loading."""

import pytest

from src.config import get


def test_required_key_exists() -> None:
    assert get("worldbank", "population_indicator") == "SP.POP.TOTL"


def test_missing_key_fails_clearly() -> None:
    with pytest.raises(KeyError, match="Missing required config key"):
        get("worldbank", "does_not_exist")
