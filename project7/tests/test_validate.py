"""Passing and failing cases for all validation checks."""

import pandas as pd
import pytest
import src.validate as validate_module

from src.validate import (
    check_total_raw, check_no_negative, check_team_unique, check_games_index,
    check_team_mapping, check_population, check_gdp, check_indicator_unique,
    check_no_aggregates, check_row_balance,
)


@pytest.mark.parametrize("check,passing,failing", [
    (check_total_raw,
     {"medals": pd.DataFrame([{"gold": 1, "silver": 2, "bronze": 3, "total_raw": 6}])},
     {"medals": pd.DataFrame([{"gold": 1, "silver": 2, "bronze": 3, "total_raw": 5}])}),
    (check_no_negative,
     {"medals": pd.DataFrame([{"gold": 1, "silver": 0, "bronze": 0}])},
     {"medals": pd.DataFrame([{"gold": -1, "silver": 0, "bronze": 0}])}),
    (check_team_unique,
     {"medals": pd.DataFrame([{"games_year": 2024, "team": "Egypt"}])},
     {"medals": pd.DataFrame([{"games_year": 2024, "team": "Egypt"}, {"games_year": 2024, "team": "Egypt"}])}),
    (check_games_index,
     {"medals": pd.DataFrame([{"games_year": 2024}]), "games_index": pd.DataFrame([{"games_year": 2024, "status": "held"}])},
     {"medals": pd.DataFrame([{"games_year": 2030}]), "games_index": pd.DataFrame([{"games_year": 2024, "status": "held"}])}),
    (check_team_mapping,
     {"medals": pd.DataFrame([{"team": "A", "country_code": "EGY"}])},
     {"medals": pd.DataFrame([{"team": "A", "country_code": None}])}),
    (check_population,
     {"indicators_long": pd.DataFrame([{"population": 100}])},
     {"indicators_long": pd.DataFrame([{"population": -1}])}),
    (check_gdp,
     {"indicators_long": pd.DataFrame([{"gdp_usd": 100}])},
     {"indicators_long": pd.DataFrame([{"gdp_usd": 0}])}),
    (check_indicator_unique,
     {"indicators_long": pd.DataFrame([{"country_code": "EGY", "year": 2024}])},
     {"indicators_long": pd.DataFrame([{"country_code": "EGY", "year": 2024}, {"country_code": "EGY", "year": 2024}])}),
    (check_no_aggregates,
     {"final": pd.DataFrame([{"country_code": "EGY"}])},
     {"final": pd.DataFrame([{"country_code": "WLD"}])}),
])
def test_validation_pass_and_fail(check, passing, failing) -> None:
    assert len(check(passing)) == 0
    assert len(check(failing)) > 0


def test_raw_final_rejected_balance_pass_and_fail(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(validate_module, "PROJECT_ROOT", tmp_path)
    reports = tmp_path / "reports"
    reports.mkdir()
    pd.DataFrame([
        {"source": "population", "raw": 10, "final": 8, "rejected": 2}
    ]).to_csv(reports / "row_counts.csv", index=False)
    assert len(check_row_balance({})) == 0
    pd.DataFrame([
        {"source": "population", "raw": 10, "final": 7, "rejected": 2}
    ]).to_csv(reports / "row_counts.csv", index=False)
    assert len(check_row_balance({})) == 1
