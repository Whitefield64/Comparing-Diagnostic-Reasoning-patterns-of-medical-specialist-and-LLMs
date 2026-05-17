"""Async NVIDIA chat-completions client for case generation."""

import asyncio
import json
import logging
import random
import time

import aiohttp

from llm_generation.config import (
    GENERATION_MAX_TOKENS,
    GENERATION_TEMPERATURE,
    NVIDIA_API_KEY,
    NVIDIA_BASE_URL,
    RATE_LIMIT_PER_MINUTE,
)

logger = logging.getLogger(__name__)

_CHAT_ENDPOINT = f"{NVIDIA_BASE_URL}/chat/completions"


class TokenBucket:
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


_bucket = TokenBucket(RATE_LIMIT_PER_MINUTE)


async def chat_completion(
    model: str,
    messages: list[dict],
    session: aiohttp.ClientSession,
    max_retries: int = 3,
) -> str | None:
    payload = {
        "model": model,
        "messages": messages,
        "temperature": GENERATION_TEMPERATURE,
        "max_tokens": GENERATION_MAX_TOKENS,
    }
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json",
    }

    for attempt in range(1, max_retries + 1):
        await _bucket.acquire()
        logger.debug(
            "Model %s: attempt %d - payload size=%d bytes",
            model,
            attempt,
            len(json.dumps(payload)),
        )
        try:
            async with session.post(
                _CHAT_ENDPOINT,
                headers=headers,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=180),
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data["choices"][0]["message"]["content"]

                body = await resp.text()
                if resp.status == 429 or resp.status >= 500:
                    retry_after = _parse_retry_after(resp.headers.get("Retry-After"))
                    wait = retry_after if retry_after is not None else 2**attempt + random.random()
                    logger.warning(
                        "Model %s attempt %d: HTTP %d, retrying in %.1fs",
                        model,
                        attempt,
                        resp.status,
                        wait,
                    )
                    await asyncio.sleep(wait)
                    continue

                logger.error("Model %s: unrecoverable HTTP %d: %s", model, resp.status, body[:300])
                return None
        except (aiohttp.ClientError, asyncio.TimeoutError) as exc:
            wait = 2**attempt + random.random()
            logger.warning("Model %s attempt %d: %s, retrying in %.1fs", model, attempt, exc, wait)
            await asyncio.sleep(wait)

    logger.error("Model %s: all retries exhausted.", model)
    return None


def _parse_retry_after(value: str | None) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except ValueError:
        return None
