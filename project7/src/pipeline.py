"""Command-line entry point for the project pipeline."""

import argparse
from collections.abc import Callable
from typing import Any

from .logging_setup import get_logger
from .ingest_worldbank import ingest_worldbank
from .validate import validate_stage

LOGGER = get_logger("pipeline")

STAGES: dict[str, Callable[..., Any]] = {}


def not_implemented(stage_name: str) -> Callable[..., None]:
    """Build a stage stub that is logged and performs no work."""
    def run(**_: Any) -> None:
        LOGGER.info("stage %s: not implemented yet", stage_name)
    return run


for stage in ["ingest", "scrape", "clean", "transform", "integrate", "analysis", "validate", "figures"]:
    STAGES[stage] = not_implemented(stage)

STAGES["ingest"] = ingest_worldbank
STAGES["validate"] = validate_stage


def parse_args() -> argparse.Namespace:
    """Parse and return command-line arguments."""
    parser = argparse.ArgumentParser(description="Olympic Games data pipeline")
    parser.add_argument("--offline", action="store_true", help="Use saved raw data only")
    parser.add_argument("--download", action="store_true", help="Allow and register downloads")
    parser.add_argument("--stage", choices=list(STAGES), help="Run one named stage")
    parser.add_argument("--sample", type=int, default=None, help="Download only N records per source")
    args = parser.parse_args()
    if args.offline and args.download:
        parser.error("--offline and --download cannot be used together")
    if args.sample is not None and args.sample < 1:
        parser.error("--sample must be a positive integer")
    return args


def main() -> int:
    """Run one or all stages."""
    args = parse_args()
    if args.stage:
        STAGES[args.stage](offline=args.offline, download=args.download, sample_n=args.sample)
    else:
        for name, stage in STAGES.items():
            stage(offline=args.offline, download=args.download, sample_n=args.sample)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
