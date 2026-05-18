"""
CLI entry point for the LLM Jury annotation system.

Usage:
    # Single case (human)
    python -m jury.run_jury "cases/2003 Case 21.md"

    # Multiple cases (human)
    python -m jury.run_jury cases/*.md

    # LLM-generated cases — pass case directories from cases_llm/
    python -m jury.run_jury --llm --output-dir jury_output_llm cases_llm/*

    # Dry run (3 voters only, for testing)
    python -m jury.run_jury --dry-run "cases/2003 Case 21.md"
    python -m jury.run_jury --llm --dry-run --output-dir jury_output_llm "cases_llm/2003 Case 21"

    # Custom number of voters
    N_VOTERS=5 python -m jury.run_jury "cases/2003 Case 21.md"

Output (human):  jury_output/{case_stem}/{case_stem}_Judge{N:03d}.json
Output (llm):    jury_output_llm/{case_stem}/{model}/{case_stem}_Judge{N:03d}.json
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

import aiohttp

from jury.config import N_VOTERS, NVIDIA_API_KEY, CONCURRENCY_LIMIT, VOTER_BATCH_SIZE, VOTER_BATCH_DELAY
from jury.preprocessor import load_case
from jury.prompt_builder import build_messages
from jury.runner import _run_voter, VoterResult
from jury.writer import write_summary, write_voter

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


async def process_case(case_path: Path, n_voters: int, case_output_dir: Path) -> None:
    logger.info("=== Processing: %s ===", case_path.name)

    full_text, reasoning_text, offset = load_case(case_path)
    logger.info(
        "PoC stripped — reasoning starts at char %d (%d chars total, %d chars reasoning)",
        offset,
        len(full_text),
        len(reasoning_text),
    )

    messages = build_messages(reasoning_text)
    # Strip model slug (after '__') so LLM case files share the same stem as their source case
    stem = case_path.stem.split("__")[0].replace(" ", "_")

    def existing_judges(out_dir: Path, stem_name: str) -> set[int]:
        if not out_dir.exists():
            return set()
        ids = set()
        for p in out_dir.glob(f"{stem_name}_Judge*.json"):
            name = p.name
            try:
                part = name.split(f"{stem_name}_Judge")[1]
                num = int(part.split(".")[0])
                ids.add(num)
            except Exception:
                continue
        return ids

    exist = existing_judges(case_output_dir, stem)
    missing = [i for i in range(1, n_voters + 1) if i not in exist]

    if not missing:
        logger.info("All %d voters already present for %s — skipping run.", n_voters, case_path.name)
        results: list[VoterResult] = []
        for vid in range(1, n_voters + 1):
            file_path = case_output_dir / f"{stem}_Judge{vid:03d}.json"
            if file_path.exists():
                try:
                    j = json.loads(file_path.read_text(encoding="utf-8"))
                    vr = VoterResult(voter_id=vid, failed=False)
                    vr.resolved = j.get("annotations", [])
                    vr.unresolved = []
                    results.append(vr)
                    continue
                except Exception:
                    pass
            vr = VoterResult(voter_id=vid, failed=True)
            results.append(vr)

        write_summary(results, case_path.name, case_output_dir, stem=stem)
        logger.info("Done: %s → %s", case_path.name, case_output_dir)
        return

    logger.info("Found %d missing voters: %s", len(missing), missing)

    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    connector = aiohttp.TCPConnector(limit=CONCURRENCY_LIMIT)

    results_map: dict[int, VoterResult] = {}
    async with aiohttp.ClientSession(connector=connector) as session:
        for batch_idx, batch_start in enumerate(range(0, len(missing), VOTER_BATCH_SIZE)):
            batch_ids = missing[batch_start : batch_start + VOTER_BATCH_SIZE]

            if batch_idx > 0:
                logger.info(
                    "Batch delay: waiting %ds before spawning next batch (%d voters)",
                    VOTER_BATCH_DELAY,
                    len(batch_ids),
                )
                await asyncio.sleep(VOTER_BATCH_DELAY)

            logger.info("Spawning batch %d: %d voters", batch_idx + 1, len(batch_ids))
            tasks = [
                _run_voter(voter_id, messages, full_text, semaphore, session)
                for voter_id in batch_ids
            ]
            batch_results = await asyncio.gather(*tasks)
            for res in batch_results:
                results_map[res.voter_id] = res
                write_voter(res, case_path.name, case_output_dir, stem=stem)

    results: list[VoterResult] = []
    for vid in range(1, n_voters + 1):
        if vid in results_map:
            results.append(results_map[vid])
            continue

        file_path = case_output_dir / f"{stem}_Judge{vid:03d}.json"
        if file_path.exists():
            try:
                j = json.loads(file_path.read_text(encoding="utf-8"))
                vr = VoterResult(voter_id=vid, failed=False)
                vr.resolved = j.get("annotations", [])
                vr.unresolved = []
                results.append(vr)
                continue
            except Exception:
                pass

        vr = VoterResult(voter_id=vid, failed=True)
        results.append(vr)

    write_summary(results, case_path.name, case_output_dir, stem=stem)
    logger.info("Done: %s → %s", case_path.name, case_output_dir)


async def main(case_output_pairs: list[tuple[Path, Path]], n_voters: int) -> None:
    for case_path, output_dir in case_output_pairs:
        await process_case(case_path, n_voters, output_dir)


def cli() -> None:
    parser = argparse.ArgumentParser(
        description="LLM Jury: annotate clinical cases with N independent LLM voters."
    )
    parser.add_argument(
        "cases",
        nargs="+",
        type=Path,
        help="Path(s) to .md case files (human mode) or case directories (--llm mode).",
    )
    parser.add_argument(
        "--llm",
        action="store_true",
        help="Accept case directories from cases_llm/ and split output by model.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("jury_output"),
        help="Base output directory (default: jury_output).",
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
            logger.error("Path not found: %s", p)
        sys.exit(1)

    if args.llm:
        # Each positional arg is a case directory; expand to (file, output_dir) pairs
        case_output_pairs: list[tuple[Path, Path]] = []
        for case_dir in args.cases:
            if not case_dir.is_dir():
                logger.error("Expected a directory in --llm mode, got: %s", case_dir)
                sys.exit(1)
            for md_file in sorted(case_dir.glob("*.md")):
                parts = md_file.stem.split("__", 1)
                case_slug = parts[0].replace(" ", "_")
                model_slug = parts[1] if len(parts) > 1 else md_file.stem
                out_dir = args.output_dir / case_slug / model_slug
                case_output_pairs.append((md_file, out_dir))
        logger.info("--llm mode: found %d case-model files across %d directories.", len(case_output_pairs), len(args.cases))
    else:
        # For human cases, append the case slug here so process_case receives the final dir
        case_output_pairs = [
            (p, args.output_dir / p.stem.replace(" ", "_"))
            for p in args.cases
        ]

    asyncio.run(main(case_output_pairs, n_voters))


if __name__ == "__main__":
    cli()
