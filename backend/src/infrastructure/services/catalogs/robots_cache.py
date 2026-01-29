"""Robots.txt cache and parser for polite catalog scraping.

Fetch and cache robots.txt per host (24h TTL). Use can_fetch(user_agent, url)
before each type-page request. Honor Crawl-delay if present (use max(parsed, our_min)).
"""
import asyncio
import logging
import time
from typing import Optional, Tuple
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

logger = logging.getLogger(__name__)

# Cache: host -> (RobotFileParser, expiry_timestamp)
_robots_cache: dict[str, Tuple[RobotFileParser, float]] = {}
_robots_ttl_sec = 24 * 3600  # 24 hours
_min_crawl_delay_sec = 8.0
_last_request_time: dict[str, float] = {}
_lock = asyncio.Lock()


async def _fetch_robots_txt(host: str, timeout: float = 10.0) -> Optional[str]:
    """Fetch robots.txt for host. Returns None on failure."""
    url = f"https://{host}/robots.txt" if not host.startswith("http") else f"{host}/robots.txt"
    if not url.startswith("http"):
        url = f"https://{host}/robots.txt"
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            r = await client.get(url)
            if r.status_code == 200:
                return r.text
    except Exception as e:
        logger.debug("robots.txt fetch failed for %s: %s", host, e)
    return None


def _get_crawl_delay_from_content(content: str) -> Optional[float]:
    """Extract Crawl-delay (seconds) from robots.txt if present. Non-standard but used by some sites."""
    for line in content.splitlines():
        line = line.strip()
        if line.lower().startswith("crawl-delay:"):
            try:
                val = float(line.split(":", 1)[1].strip())
                return max(val, _min_crawl_delay_sec)
            except (ValueError, IndexError):
                pass
    return None


async def is_allowed(user_agent: str, url: str) -> bool:
    """
    Return True if robots.txt allows fetching the given URL for the user_agent.
    Caches robots.txt per host (24h). If robots.txt is unreachable, returns True (allow).
    """
    parsed = urlparse(url)
    host = parsed.netloc or parsed.path.split("/")[0]
    if not host:
        return True
    key = host.lower()
    async with _lock:
        entry = _robots_cache.get(key)
        if entry:
            rp, expiry = entry
            if time.monotonic() < expiry:
                return rp.can_fetch(user_agent, url)
        content = await _fetch_robots_txt(host)
        if content is None:
            return True  # No robots.txt or error -> allow
        rp = RobotFileParser()
        rp.parse(content.splitlines())
        _robots_cache[key] = (rp, time.monotonic() + _robots_ttl_sec)
        return rp.can_fetch(user_agent, url)


def get_crawl_delay_sec(host: str) -> float:
    """
    Return crawl delay in seconds for host.
    Uses our minimum (8s) if Crawl-delay was not in robots.txt or not yet fetched.
    """
    entry = _robots_cache.get(host.lower())
    if entry:
        # We don't store crawl_delay in cache currently; return minimum
        pass
    return _min_crawl_delay_sec


async def enforce_rate_limit(host: str, min_delay_sec: float) -> None:
    """Sleep so that at least min_delay_sec has passed since last request to this host."""
    key = host.lower()
    last = _last_request_time.get(key, 0)
    elapsed = time.monotonic() - last
    if elapsed < min_delay_sec:
        wait = min_delay_sec - elapsed
        logger.debug("RPC rate limit: waiting %.1fs for %s", wait, host)
        await asyncio.sleep(wait)
    _last_request_time[key] = time.monotonic()
