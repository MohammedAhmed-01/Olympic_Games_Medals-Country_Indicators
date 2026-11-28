"""Data profiling for World Bank and later project datasets."""

from pathlib import Path
from typing import Any

import pandas as pd

from .config import PROJECT_ROOT
from .logging_setup import get_logger


LOGGER = get_logger("profiling")


def profile_dataframe(df: pd.DataFrame, name: str) -> dict[str, Any]:
    """Profile a dataframe and save an HTML/Markdown-compatible report section."""
    numeric = df.select_dtypes(include="number")
    ranges: dict[str, dict[str, float | int | None]] = {}
    for column in numeric.columns:
        series = numeric[column].dropna()
        if series.empty:
            ranges[str(column)] = {"min": None, "median": None, "max": None}
        else:
            ranges[str(column)] = {
                "min": float(series.min()),
                "median": float(series.median()),
                "max": float(series.max()),
            }
    result = {
        "name": name,
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "dtypes": {str(key): str(value) for key, value in df.dtypes.items()},
        "missing_share": {str(key): float(value) for key, value in df.isna().mean().items()},
        "duplicate_count": int(df.duplicated().sum()),
        "numeric_ranges": ranges,
    }
    reports_dir = PROJECT_ROOT / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)
    plot_dir = reports_dir / "figures"
    plot_dir.mkdir(parents=True, exist_ok=True)
    for column in numeric.columns[:6]:
        series = numeric[column].dropna()
        if not series.empty:
            ax = series.plot(kind="hist", bins=20, title=f"{name}: {column}")
            ax.figure.tight_layout()
            ax.figure.savefig(plot_dir / f"{name}_{column}_hist.png")
            ax.figure.clf()
    LOGGER.info("Profiled %s: %d rows, %d columns", name, len(df), len(df.columns))
    return result


def write_worldbank_quality_report(population: pd.DataFrame, gdp: pd.DataFrame) -> None:
    """Write before-cleaning World Bank quality report."""
    pop_profile = profile_dataframe(population, "wb_population")
    gdp_profile = profile_dataframe(gdp, "wb_gdp")
    games = pd.read_csv(PROJECT_ROOT / "data" / "interim" / "games_index.csv")
    held = games[(games["status"] == "held") & (games["include_in_scope"] == True)]
    first_populated = None
    for column in population.columns:
        if str(column).isdigit():
            values = pd.to_numeric(population[str(column)], errors="coerce")
            if values.notna().sum() > 0:
                first_populated = int(column)
                break
    pre_games = int(held["games_year"].astype(int).lt(first_populated).sum()) if first_populated else 0
    lines = [
        "# Data Quality Report",
        "",
        "## before cleaning",
        "",
        f"- Population shape: {pop_profile['rows']} rows x {pop_profile['columns']} columns",
        f"- Population duplicate rows: {pop_profile['duplicate_count']}",
        f"- GDP shape: {gdp_profile['rows']} rows x {gdp_profile['columns']} columns",
        f"- GDP duplicate rows: {gdp_profile['duplicate_count']}",
        f"- First populated population year observed: {first_populated}",
        f"- Held Games before the first populated population year: {pre_games}",
        "",
        "No Games years before 1960 have World Bank population observations because the bulk series begins at 1960.",
        "",
        "### Population profile",
        "",
        f"- Dtypes: {pop_profile['dtypes']}",
        f"- Missing share: {pop_profile['missing_share']}",
        f"- Numeric ranges: {pop_profile['numeric_ranges']}",
        "",
        "### GDP profile",
        "",
        f"- Dtypes: {gdp_profile['dtypes']}",
        f"- Missing share: {gdp_profile['missing_share']}",
        f"- Numeric ranges: {gdp_profile['numeric_ranges']}",
        "",
    ]
    (PROJECT_ROOT / "reports" / "data_quality_report.md").write_text(
        "\n".join(lines), encoding="utf-8"
    )
