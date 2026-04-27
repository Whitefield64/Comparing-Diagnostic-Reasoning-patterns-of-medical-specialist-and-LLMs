"""
CLI entry point for the LLM Jury annotation system.

Usage:
    # Single case
    python -m jury.run_jury "cases/2003 Case 21.md"

    # Multiple cases
    python -m jury.run_jury cases/*.md

    # Dry run (3 voters only, for testing)
    python -m jury.run_jury --dry-run "cases/2003 Case 21.md"

    # Custom number of voters
    N_VOTERS=5 python -m jury.run_jury "cases/2003 Case 21.md"

Output is written to: jury_output/{case_stem}_Judge{N:03d}.json
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from jury.config import N_VOTERS, NVIDIA_API_KEY
from jury.preprocessor import load_case
from jury.prompt_builder import build_messages
from jury.runner import run_jury
from jury.writer import write_summary, write_voter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)

OUTPUT_DIR = Path("jury_output")


async def process_case(case_path: Path, n_voters: int) -> None:
    logger.info("=== Processing: %s ===", case_path.name)

    full_text, reasoning_text, offset = load_case(case_path)
    logger.info(
        "PoC stripped — reasoning starts at char %d (%d chars total, %d chars reasoning)",
        offset,
        len(full_text),
        len(reasoning_text),
    )

    messages = build_messages(reasoning_text)
    results = await run_jury(messages, full_text, n_voters=n_voters)

    case_output_dir = OUTPUT_DIR / case_path.stem.replace(" ", "_")
    for result in results:
        write_voter(result, case_path.name, case_output_dir)

    write_summary(results, case_path.name, case_output_dir)
    logger.info("Done: %s → %s", case_path.name, case_output_dir)


async def main(case_paths: list[Path], n_voters: int) -> None:
    for case_path in case_paths:
        await process_case(case_path, n_voters)


def cli() -> None:
    parser = argparse.ArgumentParser(
        description="LLM Jury: annotate clinical cases with N independent LLM voters."
    )
    parser.add_argument(
        "cases",
        nargs="+",
        type=Path,
        help="Path(s) to .md case files.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run with 3 voters only to validate the pipeline cheaply.",
    )
    parser.add_argument(
        "--voters",
        type=int,
        default=None,
        help=f"Override number of voters (default: N_VOTERS env var or {N_VOTERS}).",
    )
    args = parser.parse_args()

    if not NVIDIA_API_KEY:
        logger.error("NVIDIA_API_KEY environment variable is not set. Aborting.")
        sys.exit(1)

    n_voters = 3 if args.dry_run else (args.voters or N_VOTERS)
    logger.info("Running with %d voter(s) per document.", n_voters)

    missing = [p for p in args.cases if not p.exists()]
    if missing:
        for p in missing:
            logger.error("File not found: %s", p)
        sys.exit(1)

    asyncio.run(main(args.cases, n_voters))


if __name__ == "__main__":
    cli()
