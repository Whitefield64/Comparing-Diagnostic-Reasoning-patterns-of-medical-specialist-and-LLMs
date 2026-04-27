"""
Orchestrate N_VOTERS independent LLM calls for a single document.

Each voter receives the same prompt (but temperature > 0 produces variance).
Results are collected concurrently, limited to CONCURRENCY_LIMIT active requests.
"""

import asyncio
import logging
from dataclasses import dataclass, field

import aiohttp

from jury.config import CONCURRENCY_LIMIT, N_VOTERS
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
) -> VoterResult:
    result = VoterResult(voter_id=voter_id)
    async with semaphore:
        logger.info("Voter %03d starting…", voter_id)
        raw = await chat_completion(messages, voter_id, session)

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
    Launch n_voters concurrent requests and return their results.
    """
    semaphore = asyncio.Semaphore(CONCURRENCY_LIMIT)
    connector = aiohttp.TCPConnector(limit=CONCURRENCY_LIMIT)

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = [
            _run_voter(voter_id, messages, full_text, semaphore, session)
            for voter_id in range(1, n_voters + 1)
        ]
        results = await asyncio.gather(*tasks)

    successful = sum(1 for r in results if not r.failed)
    logger.info("Jury complete: %d/%d voters succeeded.", successful, n_voters)
    return list(results)
