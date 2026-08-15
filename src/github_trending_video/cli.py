from __future__ import annotations

import argparse
import logging
import sys

from .config import Settings
from .pipeline import Pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create a unique daily GitHub Trending video research package."
    )
    parser.add_argument("--config", help="Path to an optional JSON configuration file")
    parser.add_argument("--run-id", help="Output identifier; defaults to today's YYYY-MM-DD")
    parser.add_argument("--dry-run", action="store_true", help="Do not update featured history")
    parser.add_argument(
        "--no-llm",
        action="store_true",
        help="Create a limited deterministic report without an LLM",
    )
    parser.add_argument("--skip-images", action="store_true", help="Do not download README media")
    parser.add_argument("--verbose", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )
    try:
        settings = Settings.load(args.config)
        result = Pipeline(settings, no_llm=args.no_llm, skip_images=args.skip_images).run(
            run_id=args.run_id,
            dry_run=args.dry_run,
        )
        print(result)
        return 0
    except Exception as exc:
        logging.error("Pipeline failed: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
