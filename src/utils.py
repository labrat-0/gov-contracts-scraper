"""Utility functions for rate limiting, retries, and HTTP helpers."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

# SAM.gov API rate limits vary by role.
# Non-federal users: conservative interval to stay safe.
REQUEST_INTERVAL = 1.0  # Government API -- no anti-bot, but be polite

# Retry settings
MAX_RETRIES = 3
RETRY_BASE_DELAY = 5.0  # seconds

# API base URLs
SAM_OPPORTUNITIES_URL = "https://api.sam.gov/opportunities/v2/search"
SAM_FEDERAL_HIERARCHY_URL = "https://api.sam.gov/prod/federalorganizations/v1/orgs"


class RateLimiter:
    """Simple rate limiter that ensures a minimum interval between requests."""

    def __init__(self, interval: float = REQUEST_INTERVAL) -> None:
        self._interval = interval
        self._last_request: float = 0.0
        self._lock = asyncio.Lock()

    async def wait(self) -> None:
        """Wait until it's safe to make another request."""
        async with self._lock:
            now = asyncio.get_event_loop().time()
            elapsed = now - self._last_request
            if elapsed < self._interval:
                wait_time = self._interval - elapsed
                logger.debug(f"Rate limiter: waiting {wait_time:.1f}s")
                await asyncio.sleep(wait_time)
            self._last_request = asyncio.get_event_loop().time()


async def fetch_json(
    client: httpx.AsyncClient,
    url: str,
    rate_limiter: RateLimiter,
    params: dict[str, Any] | None = None,
) -> dict[str, Any] | list[Any] | None:
    """Fetch JSON from a URL with rate limiting and retry logic.

    Returns the parsed JSON data, or None if all retries fail.
    """
    for attempt in range(MAX_RETRIES):
        await rate_limiter.wait()

        try:
            response = await client.get(
                url,
                params=params,
                timeout=30.0,
                follow_redirects=True,
            )

            if response.status_code == 200:
                return response.json()

            if response.status_code == 429:
                delay = RETRY_BASE_DELAY * (2 ** attempt)
                logger.warning(
                    f"Rate limited (429) on {url}. "
                    f"Retrying in {delay}s (attempt {attempt + 1}/{MAX_RETRIES})"
                )
                await asyncio.sleep(delay)
                continue

            if response.status_code == 403:
                logger.error(
                    f"Forbidden (403) on {url}. "
                    "Your API key may be invalid or expired."
                )
                return None

            if response.status_code == 400:
                logger.error(
                    f"Bad request (400) on {url}. "
                    f"Response: {response.text[:500]}"
                )
                return None

            if response.status_code == 404:
                logger.warning(f"Not found (404): {url}")
                return None

            if response.status_code >= 500:
                delay = 10.0 * (attempt + 1)
                logger.warning(
                    f"Server error ({response.status_code}) on {url}. "
                    f"Retrying in {delay}s (attempt {attempt + 1}/{MAX_RETRIES})"
                )
                await asyncio.sleep(delay)
                continue

            logger.warning(
                f"Unexpected status {response.status_code} on {url}. "
                f"Response: {response.text[:300]}"
            )
            return None

        except httpx.TimeoutException:
            delay = 10.0 * (attempt + 1)
            logger.warning(
                f"Timeout on {url}. "
                f"Retrying in {delay}s (attempt {attempt + 1}/{MAX_RETRIES})"
            )
            await asyncio.sleep(delay)
            continue

        except httpx.HTTPError as e:
            delay = 10.0 * (attempt + 1)
            logger.warning(
                f"HTTP error on {url}: {e}. "
                f"Retrying in {delay}s (attempt {attempt + 1}/{MAX_RETRIES})"
            )
            await asyncio.sleep(delay)
            continue

    logger.error(f"All {MAX_RETRIES} retries exhausted for {url}")
    return None
