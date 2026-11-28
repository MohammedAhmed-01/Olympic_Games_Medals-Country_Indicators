"""Generate the Summer Olympics games index."""

import time
from pathlib import Path

import pandas as pd
import requests

from .config import PROJECT_ROOT, get
from .logging_setup import get_logger


LOGGER = get_logger("games_index")


def build_games_index(download_status: bool = True) -> pd.DataFrame:
    """Build one row per Summer Games event through 2024."""
    held = list(range(1896, 1917, 4)) + list(range(1920, 1940, 4))
    held += [1948, 1952, 1956, 1960, 1964, 1968, 1972, 1976, 1980, 1984,
             1988, 1992, 1996, 2000, 2004, 2008, 2012, 2016, 2020, 2024]
    rows: list[dict[str, object]] = []
    cancelled = {1916, 1940, 1944}
    for year in sorted(set(held) | cancelled | {1906}):
        status = "intercalated" if year == 1906 else ("cancelled" if year in cancelled else "held")
        held_year = 2021 if year == 2020 else year
        table_url = str(get("scraper", "games_url_template")).format(year=year)
        page_url = str(get("scraper", "games_page_template")).format(year=year)
        if status == "held":
            url = table_url
            note = ""
        else:
            url = page_url
            note = "Games cancelled" if status == "cancelled" else "Intercalated Games"
        if year == 2020:
            note = "Tokyo 2020 Games held in 2021"
        if download_status:
            headers = {"User-Agent": str(get("scraper", "user_agent"))}
            response = requests.get(url, headers=headers, timeout=30)
            primary_status = response.status_code
            LOGGER.info("Checked %s: HTTP %d", url, primary_status)
            time.sleep(float(get("scraper", "delay_seconds")))
            if primary_status != 200:
                fallback_url = page_url if url == table_url else table_url
                fallback = requests.get(fallback_url, headers=headers, timeout=30)
                fallback_status = fallback.status_code
                LOGGER.info("Checked fallback %s: HTTP %d", fallback_url, fallback_status)
                time.sleep(float(get("scraper", "delay_seconds")))
                if fallback_status != 200:
                    raise RuntimeError(
                        f"Both Games URLs failed for {year}: "
                        f"HTTP {primary_status} ({url}), HTTP {fallback_status} ({fallback_url})"
                    )
                url = fallback_url
                note = f"{note}; " if note else ""
                note += (
                    f"HTTP {primary_status} at primary URL; HTTP {fallback_status} at fallback URL"
                )
                if url == page_url:
                    note += "; table inside main page"
            else:
                note = f"{note}; " if note else ""
                note += f"HTTP {primary_status}"
        games_name = f"{held_year if held_year != year else year} Summer Olympics"
        start = get("twist", "games_range").get("start")
        end = get("twist", "games_range").get("end")
        include = status == "held" and (start is None or year >= int(start)) and (end is None or year <= int(end))
        rows.append({
            "games_year": year,
            "held_year": held_year,
            "games_name": games_name,
            "url": url,
            "status": status,
            "include_in_scope": include,
            "notes": note,
        })
    frame = pd.DataFrame(rows, columns=[
        "games_year", "held_year", "games_name", "url", "status", "include_in_scope", "notes"
    ])
    output = PROJECT_ROOT / "data" / "interim" / "games_index.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output, index=False, encoding="utf-8")
    LOGGER.info("Wrote games index: %s rows", len(frame))
    return frame
