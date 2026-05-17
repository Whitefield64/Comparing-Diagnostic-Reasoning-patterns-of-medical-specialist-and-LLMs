"""
CLI entry point for generating LLM differential diagnoses.

Usage:
    python -m llm_generation.run_generation "cases/2003 Case 39.md"
    python -m llm_generation.run_generation --models model_a,model_b,model_c cases/*.md
    python -m llm_generation.run_generation --dry-run "cases/2003 Case 39.md"
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path

from llm_generation.config import GENERATION_MODELS, GENERATION_OUTPUT_DIR, NVIDIA_API_KEY
from llm_generation.preprocessor import load_presentation
from llm_generation.runner import generate_for_case

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


async def main(
    case_paths: list[Path],
    models: list[str],
    output_dir: Path,
    overwrite: bool,
) -> None:
    for case_path in case_paths:
        case = load_presentation(case_path)
        logger.info(
            "Loaded presentation for %s (%d chars)",
            case.source_case_name,
            len(case.presentation_text),
        )
        results = await generate_for_case(case, models, output_dir, overwrite)
        failed = [result.model for result in results if result.failed]
        if failed:
            logger.warning("Failed models for %s: %s", case.source_case_name, ", ".join(failed))


def cli() -> None:
    parser = argparse.ArgumentParser(
        description="Generate LLM differential diagnoses from Presentation of Case sections."
    )
    parser.add_argument("cases", nargs="+", type=Path, help="Path(s) to source .md case files.")
    parser.add_argument(
        "--models",
        type=str,
        default=None,
        help="Comma-separated model names. Defaults to GENERATION_MODELS or NVIDIA_MODEL from .env.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=GENERATION_OUTPUT_DIR,
        help=f"Output directory (default: {GENERATION_OUTPUT_DIR}).",
    )
    parser.add_argument("--overwrite", action="store_true", help="Regenerate files that already exist.")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Use only the first case and first configured model.",
    )
    args = parser.parse_args()

    if not NVIDIA_API_KEY:
        logger.error("NVIDIA_API_KEY environment variable is not set. Aborting.")
        sys.exit(1)

    missing = [path for path in args.cases if not path.exists()]
    if missing:
        for path in missing:
            logger.error("File not found: %s", path)
        sys.exit(1)

    models = _parse_models(args.models) if args.models else GENERATION_MODELS
    if not models:
        logger.error("No generation models configured.")
        sys.exit(1)

    case_paths = args.cases
    if args.dry_run:
        case_paths = case_paths[:1]
        models = models[:1]
        logger.info("Dry run: using one case and one model.")

    logger.info("Generation models: %s", ", ".join(models))
    asyncio.run(main(case_paths, models, args.output_dir, args.overwrite))


def _parse_models(value: str) -> list[str]:
    return [model.strip() for model in value.split(",") if model.strip()]


if __name__ == "__main__":
    cli()
