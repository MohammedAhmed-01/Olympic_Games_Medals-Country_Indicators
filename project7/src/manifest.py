"""Raw-file manifest registration and integrity verification."""

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from .config import PROJECT_ROOT


MANIFEST_PATH = PROJECT_ROOT / "data" / "raw" / "MANIFEST.csv"
COLUMNS = ["path", "source_url", "retrieved_at_utc", "sha256", "size_bytes", "rows", "notes"]


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _display_path(path: Path) -> str:
    resolved = path.resolve()
    try:
        return resolved.relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return str(resolved)


def register_file(path: str | Path, source_url: str, retrieved_at_utc: str,
                  rows: int, notes: str) -> dict[str, Any]:
    """Register original bytes by appending a manifest row."""
    file_path = Path(path)
    if not file_path.is_absolute():
        file_path = PROJECT_ROOT / file_path
    if not file_path.exists():
        raise FileNotFoundError(f"Cannot register missing file: {file_path}")
    MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    write_header = not MANIFEST_PATH.exists()
    row = {
        "path": _display_path(file_path),
        "source_url": source_url,
        "retrieved_at_utc": retrieved_at_utc,
        "sha256": _sha256(file_path),
        "size_bytes": file_path.stat().st_size,
        "rows": int(rows),
        "notes": notes,
    }
    frame = pd.DataFrame([row], columns=COLUMNS)
    frame.to_csv(MANIFEST_PATH, mode="a", index=False, header=write_header, encoding="utf-8")
    return row


def verify_manifest() -> None:
    """Verify latest manifest row for each path."""
    if not MANIFEST_PATH.exists():
        raise FileNotFoundError(f"Manifest does not exist: {MANIFEST_PATH}")
    manifest = pd.read_csv(MANIFEST_PATH)
    latest = manifest.drop_duplicates(subset=["path"], keep="last")
    mismatches: list[str] = []
    for row in latest.to_dict("records"):
        raw_path = PROJECT_ROOT / str(row["path"])
        if not raw_path.exists():
            mismatches.append(f"{row['path']}: missing")
            continue
        actual = _sha256(raw_path)
        if actual != str(row["sha256"]):
            mismatches.append(f"{row['path']}: hash mismatch")
    if mismatches:
        raise ValueError("Manifest verification failed:\n" + "\n".join(mismatches))
