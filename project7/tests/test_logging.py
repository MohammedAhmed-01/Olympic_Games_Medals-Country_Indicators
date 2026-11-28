"""Tests for UTC logging."""

from src.logging_setup import get_logger


def test_log_line_uses_utc_timestamp(tmp_path) -> None:
    logger = get_logger("utc_test")
    logger.info("UTC timestamp test")
    log_path = __import__("src.config", fromlist=["PROJECT_ROOT"]).PROJECT_ROOT / "logs" / "pipeline.log"
    text = log_path.read_text(encoding="utf-8")
    assert "Z " in text
