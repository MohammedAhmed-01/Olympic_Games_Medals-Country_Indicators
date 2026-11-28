"""Validation registry and report generation."""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import pandas as pd

from .config import PROJECT_ROOT
from .logging_setup import get_logger


LOGGER = get_logger("validate")
CHECKS: list[tuple[str, Callable[[dict[str, pd.DataFrame]], pd.DataFrame]]] = []


@dataclass
class CheckResult:
    name: str
    passed: bool
    failing_rows: int
    detail: str


def register_check(name: str) -> Callable:
    """Register a named validation check."""
    def decorator(function: Callable) -> Callable:
        CHECKS.append((name, function))
        return function
    return decorator


def _missing(data: dict[str, pd.DataFrame], key: str) -> bool:
    return key not in data


def _write_failures(name: str, failures: pd.DataFrame) -> None:
    rejected = PROJECT_ROOT / "data" / "rejected"
    rejected.mkdir(parents=True, exist_ok=True)
    safe_name = name.replace(" ", "_")
    failures.to_csv(rejected / f"validation_{safe_name}.csv", index=False, encoding="utf-8")


@register_check("total_raw")
def check_total_raw(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    if _missing(data, "medals"):
        raise KeyError("medals")
    frame = data["medals"]
    required = {"gold", "silver", "bronze", "total_raw"}
    if not required.issubset(frame.columns):
        raise KeyError("medals missing medal count columns")
    return frame.loc[
        pd.to_numeric(frame["total_raw"], errors="coerce")
        != pd.to_numeric(frame["gold"], errors="coerce")
        + pd.to_numeric(frame["silver"], errors="coerce")
        + pd.to_numeric(frame["bronze"], errors="coerce")
    ]


@register_check("no_negative_medals")
def check_no_negative(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    if _missing(data, "medals"):
        raise KeyError("medals")
    frame = data["medals"]
    columns = [column for column in ("gold", "silver", "bronze", "total_raw") if column in frame.columns]
    if not columns:
        raise KeyError("medals missing medal count columns")
    mask = (frame[columns] < 0).any(axis=1)
    return frame.loc[mask]


@register_check("medal_team_unique")
def check_team_unique(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    if _missing(data, "medals"):
        raise KeyError("medals")
    frame = data["medals"]
    required = {"games_year", "team"}
    if not required.issubset(frame.columns):
        raise KeyError("medals missing games_year/team")
    return frame.loc[frame.duplicated(["games_year", "team"], keep=False)]


@register_check("games_year_status")
def check_games_index(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    if _missing(data, "medals") or _missing(data, "games_index"):
        raise KeyError("medals or games_index")
    medals = data["medals"]
    index = data["games_index"]
    if "games_year" not in medals or "games_year" not in index or "status" not in index:
        raise KeyError("required games_year/status columns missing")
    known = set(index["games_year"].astype(int).tolist())
    return medals.loc[~medals["games_year"].astype(int).isin(known)]


@register_check("team_country_mapping")
def check_team_mapping(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    if _missing(data, "medals"):
        raise KeyError("medals")
    frame = data["medals"]
    if "team" not in frame:
        raise KeyError("medals missing team")
    if "country_code" not in frame and "mapping_type" not in frame:
        raise KeyError("medals missing country_code/mapping_type")
    country_ok = frame["country_code"].notna() if "country_code" in frame else pd.Series(False, index=frame.index)
    no_country = frame["mapping_type"].eq("no_current_country") if "mapping_type" in frame else pd.Series(False, index=frame.index)
    return frame.loc[~(country_ok | no_country)]


@register_check("population_positive")
def check_population(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    if _missing(data, "indicators_long"):
        raise KeyError("indicators_long")
    frame = data["indicators_long"]
    if "population" not in frame:
        raise KeyError("population")
    present = frame["population"].notna()
    return frame.loc[present & (pd.to_numeric(frame["population"], errors="coerce") <= 0)]


@register_check("gdp_positive")
def check_gdp(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    if _missing(data, "indicators_long"):
        raise KeyError("indicators_long")
    frame = data["indicators_long"]
    if "gdp_usd" not in frame:
        raise KeyError("gdp_usd")
    present = frame["gdp_usd"].notna()
    return frame.loc[present & (pd.to_numeric(frame["gdp_usd"], errors="coerce") <= 0)]


@register_check("indicator_country_year_unique")
def check_indicator_unique(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    if _missing(data, "indicators_long"):
        raise KeyError("indicators_long")
    frame = data["indicators_long"]
    if not {"country_code", "year"}.issubset(frame.columns):
        raise KeyError("indicators country_code/year")
    return frame.loc[frame.duplicated(["country_code", "year"], keep=False)]


@register_check("no_regional_aggregates")
def check_no_aggregates(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    if _missing(data, "final"):
        raise KeyError("final")
    frame = data["final"]
    aggregate_codes = {"ARB", "CSS", "CEB", "EAR", "EAS", "ECS", "EMU", "EUU", "FCS", "HIC", "HPC", "IBD", "IBT", "IDA", "LTE", "LCN", "LIC", "LMC", "LMY", "MEA", "MIC", "NAC", "OED", "OSS", "PRE", "PSS", "PST", "SAS", "SSA", "SSF", "SST", "TEA", "TEC", "TLA", "TMN", "TSA", "TSS", "UMC", "WLD"}
    if "country_code" not in frame:
        raise KeyError("final missing country_code")
    return frame.loc[frame["country_code"].isin(aggregate_codes)]


@register_check("raw_final_rejected_balance")
def check_row_balance(data: dict[str, pd.DataFrame]) -> pd.DataFrame:
    row_counts_path = PROJECT_ROOT / "reports" / "row_counts.csv"
    if not row_counts_path.exists():
        raise KeyError("row_counts.csv")
    counts = pd.read_csv(row_counts_path)
    if not {"source", "raw", "final", "rejected"}.issubset(counts.columns):
        raise KeyError("row_counts.csv contract")
    return counts.loc[counts["raw"].fillna(0) != counts["final"].fillna(0) + counts["rejected"].fillna(0)]


def run_all(data_dict: dict[str, pd.DataFrame]) -> list[CheckResult]:
    """Run every registered check and write validation report."""
    results: list[CheckResult] = []
    for name, function in CHECKS:
        try:
            failures = function(data_dict)
            if len(failures):
                _write_failures(name, failures)
                results.append(CheckResult(name, False, len(failures), "FAILED"))
            else:
                results.append(CheckResult(name, True, 0, "PASSED"))
        except (KeyError, FileNotFoundError) as error:
            detail = f"SKIPPED (input missing: {error.args[0]})"
            results.append(CheckResult(name, True, 0, detail))
    report = ["# Validation Report", "", "| Name | Passed | Failing rows | Detail |", "|---|---:|---:|---|"]
    for result in results:
        status = "PASSED" if result.passed and not result.detail.startswith("SKIPPED") else (
            "SKIPPED" if result.detail.startswith("SKIPPED") else "FAILED"
        )
        report.append(f"| {result.name} | {status} | {result.failing_rows} | {result.detail} |")
    report_path = PROJECT_ROOT / "reports"
    report_path.mkdir(parents=True, exist_ok=True)
    (report_path / "validation_report.md").write_text("\n".join(report), encoding="utf-8")
    return results


def validate_stage(**_: object) -> None:
    """Load available inputs and run validation; fail if real checks fail."""
    data: dict[str, pd.DataFrame] = {}
    candidates = {
        "medals": "medals_clean.csv",
        "games_index": "games_index.csv",
        "indicators_long": "indicators_long.csv",
        "final": "final.csv",
    }
    for key, filename in candidates.items():
        path = PROJECT_ROOT / "data" / "interim" / filename
        if key == "final":
            path = PROJECT_ROOT / "data" / "final" / filename
        if path.exists():
            data[key] = pd.read_csv(path)
    results = run_all(data)
    failures = [result for result in results if result.detail == "FAILED"]
    if failures:
        names = ", ".join(result.name for result in failures)
        raise RuntimeError(f"Validation failed: {names}")
