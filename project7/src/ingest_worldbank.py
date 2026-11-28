"""World Bank bulk CSV ingestion and raw-file registration."""

import io
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd
import requests

from .config import PROJECT_ROOT, get
from .logging_setup import get_logger
from .manifest import register_file, verify_manifest


LOGGER = get_logger("ingest_worldbank")


def utc_now() -> str:
    """Return an ISO 8601 UTC timestamp."""
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _download(url: str, timeout: int = 30) -> bytes:
    LOGGER.info("Downloading %s", url)
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    return response.content


def _find_data_csv(directory: Path, indicator: str) -> Path:
    candidates = list(directory.glob(f"API_{indicator}_*_csv_v2_*.csv"))
    if not candidates:
        candidates = list(directory.glob(f"*{indicator}*.csv"))
    for candidate in candidates:
        if candidate.name.startswith("API_"):
            return candidate
    raise FileNotFoundError(f"No World Bank data CSV found for {indicator}")


def _process_csv(csv_path: Path, output_name: str, skiprows: int,
                 sample_n: int | None) -> pd.DataFrame:
    LOGGER.info("Reading %s shape before parsing: unknown", csv_path)
    frame = pd.read_csv(csv_path, skiprows=skiprows)
    LOGGER.info("Shape after read_csv: %s", frame.shape)
    unnamed = [column for column in frame.columns if str(column).startswith("Unnamed")]
    if unnamed:
        LOGGER.info("Dropping trailing empty columns: %s", unnamed)
        frame = frame.drop(columns=unnamed)
    year_columns = [column for column in frame.columns if str(column).isdigit()]
    for column in year_columns:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    if sample_n is not None:
        frame = frame.iloc[:sample_n].copy()
    output_path = PROJECT_ROOT / "data" / "interim" / output_name
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False, encoding="utf-8")
    LOGGER.info("Shape after cleaning: %s", frame.shape)
    return frame


def ingest_worldbank(offline: bool = False, download: bool = False,
                     sample_n: int | None = None, **_: Any) -> None:
    """Download or reuse both World Bank bulk indicators."""
    population_indicator = str(get("worldbank", "population_indicator"))
    gdp_indicator = str(get("worldbank", "gdp_indicator"))
    template = str(get("worldbank", "download_url_template"))
    skiprows = int(get("worldbank", "skiprows"))
    raw_dir = PROJECT_ROOT / "data" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    indicators = [
        (population_indicator, "wb_population_raw.csv", "SP.POP.TOTL.zip"),
        (gdp_indicator, "wb_gdp_raw.csv", "NY.GDP.MKTP.CD.zip"),
    ]
    for indicator, output_name, zip_name in indicators:
        zip_path = raw_dir / zip_name
        extracted_dir = raw_dir / zip_name.replace(".zip", "")
        if download or not offline and not zip_path.exists():
            url = template.format(indicator=indicator)
            content = _download(url)
            zip_path.write_bytes(content)
            register_file(zip_path, url, utc_now(), 0, f"Original World Bank CSV ZIP for {indicator}")
            extracted_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(io.BytesIO(content), "r") as archive:
                for member in archive.namelist():
                    destination = extracted_dir / Path(member).name
                    destination.write_bytes(archive.read(member))
            for extracted in sorted(extracted_dir.iterdir()):
                if extracted.is_file():
                    row_count = 0
                    if extracted.suffix.lower() == ".csv":
                        with extracted.open("r", encoding="utf-8-sig") as handle:
                            row_count = max(0, sum(1 for _ in handle) - 1)
                    register_file(extracted, url, utc_now(), row_count,
                                  f"Extracted original CSV for {indicator}")
        elif zip_path.exists():
            LOGGER.info("Offline mode: using saved raw ZIP %s", zip_path)
            extracted_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(zip_path, "r") as archive:
                for member in archive.namelist():
                    destination = extracted_dir / Path(member).name
                    if not destination.exists():
                        destination.write_bytes(archive.read(member))
        else:
            raise FileNotFoundError(
                f"Offline mode has no saved raw file for {indicator}: {zip_path}"
            )
        verify_manifest()
        data_csv = _find_data_csv(extracted_dir, indicator)
        _process_csv(data_csv, output_name, skiprows, sample_n)
