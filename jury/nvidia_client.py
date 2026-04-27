"""
Async NVIDIA Build API client with token-bucket rate limiting.

Rate limit: 40 requests/minute → one token every 1.5 seconds.
Retries up to 3 times with exponential backoff on 429 or 5xx responses.
"""

import asyncio
import json
import logging
import time

import aiohttp

from jury.config import (
    MAX_TOKENS,
    NVIDIA_API_KEY,
    NVIDIA_BASE_URL,
    NVIDIA_MODEL,
    RATE_LIMIT_PER_MINUTE,
    TEMPERATURE,
)

logger = logging.getLogger(__name__)

_CHAT_ENDPOINT = f"{NVIDIA_BASE_URL}/chat/completions"


class TokenBucket:
    """Leaky-bucket rate limiter for async code."""

    def __init__(self, rate_per_minute: int) -> None:
        self._interval = 60.0 / rate_per_minute
        self._last_call = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            wait = self._interval - (now - self._last_call)
            if wait > 0:
                await asyncio.sleep(wait)
            self._last_call = time.monotonic()


# Module-level singleton so all callers share the same bucket.
_bucket = TokenBucket(RATE_LIMIT_PER_MINUTE)


async def chat_completion(
    messages: list[dict],
    voter_id: int,
    session: aiohttp.ClientSession,
    max_retries: int = 3,
) -> str | None:
    """
    Call the NVIDIA chat completions endpoint and return the assistant message content.
    Returns None if all retries are exhausted.
    """
    payload = {
        "model": NVIDIA_MODEL,
        "messages": messages,
        "temperature": TEMPERATURE,
        "max_tokens": MAX_TOKENS,
    }
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json",
    }

    for attempt in range(1, max_retries + 1):
        await _bucket.acquire()
        try:
            async with session.post(
                _CHAT_ENDPOINT,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=120),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]

                body = await resp.text()
                if resp.status == 429 or resp.status >= 500:
                    wait = 2**attempt
                    logger.warning(
                        "Voter %d attempt %d: HTTP %d — retrying in %ds",
                        voter_id,
                        attempt,
                        resp.status,
                        wait,
                    )
                    await asyncio.sleep(wait)
                else:
                    logger.error(
                        "Voter %d: unrecoverable HTTP %d: %s",
                        voter_id,
                        resp.status,
                        body[:200],
                    )
                    return None

        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            wait = 2**attempt
            logger.warning(
                "Voter %d attempt %d: %s — retrying in %ds",
                voter_id,
                attempt,
                exc,
                wait,
            )
            await asyncio.sleep(wait)

    logger.error("Voter %d: all retries exhausted.", voter_id)
    return None


def parse_response(content: str) -> list[dict] | None:
    """
    Extract the JSON array from the LLM response.
    The model is instructed to return ONLY JSON, but may wrap it in markdown code fences.
    """
    if content is None:
        return None

    text = content.strip()

    # Strip optional markdown fences
    if text.startswith("```"):
        lines = text.splitlines()
        # Drop first line (```json or ```) and last line (```)
        inner = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        text = inner.strip()

    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
        # Some models wrap the array in {"annotations": [...]}
        if isinstance(parsed, dict):
            for key in ("annotations", "results", "spans"):
                if isinstance(parsed.get(key), list):
                    return parsed[key]
    except json.JSONDecodeError:
        logger.warning("Could not parse JSON from model response: %s", content[:300])

    return None
