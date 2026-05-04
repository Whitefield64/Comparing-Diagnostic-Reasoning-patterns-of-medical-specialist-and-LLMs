"""
Orchestrate N_VOTERS independent LLM calls for a single document.

Each voter receives the same prompt (but temperature > 0 produces variance).
Results are collected concurrently, limited to CONCURRENCY_LIMIT active requests.
"""

import asyncio
import logging
from dataclasses import dataclass, field

import aiohttp

from jury.config import CONCURRENCY_LIMIT, N_VOTERS, VOTER_BATCH_SIZE, VOTER_BATCH_DELAY
from jury.nvidia_client import chat_completion, parse_response
from jury.offset_resolver import resolve

logger = logging.getLogger(__name__)


@dataclass
class VoterResult:
    voter_id: int
    raw_response: str | None = None
    raw_annotations: list[dict] = field(default_factory=list)
    resolved: list[dict] = field(default_factory=list)
    unresolved: list[dict] = field(default_factory=list)
    failed: bool = False


async def _run_voter(
    voter_id: int,
    messages: list[dict],
    full_text: str,
    semaphore: asyncio.Semaphore,
    session: aiohttp.ClientSession,
    model: str | None = None,
) -> VoterResult:
    result = VoterResult(voter_id=voter_id)
    async with semaphore:
        logger.info("Voter %03d starting…", voter_id)
        raw = await chat_completion(messages, voter_id, session, model=model)

    if raw is None:
        result.failed = True
        logger.error("Voter %03d failed (no response).", voter_id)
        return result

    result.raw_response = raw
    parsed = parse_response(raw)

    if parsed is None:
        result.failed = True
        logger.error("Voter %03d failed (unparseable JSON).", voter_id)
        return result

    result.raw_annotations = parsed
    result.resolved, result.unresolved = resolve(parsed, full_text)
    logger.info(
        "Voter %03d: %d resolved, %d unresolved.",
        voter_id,
        len(result.resolved),
        len(result.unresolved),
    )
    return result


async def run_jury(
    messages: list[dict],
    full_text: str,
    n_voters: int = N_VOTERS,
) -> list[VoterResult]:
    """
    Launch n_voters concurrent requests, staggered in batches to reduce burst load.
    """
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    connector = aiohttp.TCPConnector(limit=CONCURRENCY_LIMIT)
    results: list[VoterResult] = []

    async with aiohttp.ClientSession(connector=connector) as session:
        # Batch voters to avoid thundering herd on remote API
        for batch_idx in range(0, n_voters, VOTER_BATCH_SIZE):
            batch_ids = range(batch_idx + 1, min(batch_idx + VOTER_BATCH_SIZE + 1, n_voters + 1))
            
            if batch_idx > 0:
                logger.info(
                    "Batch delay: waiting %ds before spawning voters %d-%d",
                    VOTER_BATCH_DELAY,
                    batch_ids.start,
                    batch_ids.stop - 1,
                )
                await asyncio.sleep(VOTER_BATCH_DELAY)
            
            logger.info("Spawning batch: voters %d-%d", batch_ids.start, batch_ids.stop - 1)
            tasks = [
                _run_voter(voter_id, messages, full_text, semaphore, session)
                for voter_id in batch_ids
            ]
            batch_results = await asyncio.gather(*tasks)
            results.extend(batch_results)

    successful = sum(1 for r in results if not r.failed)
    logger.info("Jury complete: %d/%d voters succeeded.", successful, n_voters)
    return list(results)
