"""Run model generations for one source case."""

import asyncio
import logging
import re
from dataclasses import dataclass
from pathlib import Path

import aiohttp

from llm_generation.client import chat_completion
from llm_generation.config import (
    CONCURRENCY_LIMIT,
    GENERATION_EXPANSION_ATTEMPTS,
    GENERATION_MIN_WORDS,
    GENERATION_OUTPUT_DIR,
)
from llm_generation.preprocessor import CasePresentation
from llm_generation.prompt_builder import build_expansion_messages, build_messages
from llm_generation.writer import output_path, write_generated_case

logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    model: str
    output_path: Path | None = None
    skipped: bool = False
    failed: bool = False


async def generate_for_case(
    case: CasePresentation,
    models: list[str],
    output_dir: Path = GENERATION_OUTPUT_DIR,
    overwrite: bool = False,
) -> list[GenerationResult]:
    messages = build_messages(case)
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    connector = aiohttp.TCPConnector(limit=CONCURRENCY_LIMIT)

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [
            _generate_one(case, model, messages, session, semaphore, output_dir, overwrite)
            for model in models
        ]
        return await asyncio.gather(*tasks)


async def _generate_one(
    case: CasePresentation,
    model: str,
    messages: list[dict],
    session: aiohttp.ClientSession,
    semaphore: asyncio.Semaphore,
    output_dir: Path,
    overwrite: bool,
) -> GenerationResult:
    out_path = output_path(case, model, output_dir)
    if out_path.exists() and not overwrite:
        logger.info("Skipping existing generation: %s", out_path)
        return GenerationResult(model=model, output_path=out_path, skipped=True)

    async with semaphore:
        logger.info("Generating %s with %s", case.source_case_name, model)
        generated = await chat_completion(model, messages, session)

    if generated is None:
        return GenerationResult(model=model, failed=True)

    best_generated = generated
    best_word_count = _word_count(generated)

    for attempt in range(1, GENERATION_EXPANSION_ATTEMPTS + 1):
        word_count = _word_count(generated)
        if word_count > best_word_count:
            best_generated = generated
            best_word_count = word_count

        if word_count >= GENERATION_MIN_WORDS:
            break

        logger.info(
            "Generated draft from %s is short (%d words); requesting expansion attempt %d/%d to at least %d words.",
            model,
            word_count,
            attempt,
            GENERATION_EXPANSION_ATTEMPTS,
            GENERATION_MIN_WORDS,
        )
        expansion_messages = build_expansion_messages(case, generated, GENERATION_MIN_WORDS, word_count)
        expanded = await chat_completion(model, expansion_messages, session)
        if expanded is not None:
            generated = expanded

    if _word_count(generated) > best_word_count:
        best_generated = generated
        best_word_count = _word_count(generated)

    if best_generated is not generated:
        logger.info(
            "Using longest available generation from %s (%d words).",
            model,
            best_word_count,
        )
        generated = best_generated

    written = write_generated_case(case, model, generated, output_dir)
    logger.info("Written: %s", written)
    return GenerationResult(model=model, output_path=written)


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))
