import asyncio
import logging
import time
from abc import ABC, abstractmethod
from typing import Optional, Callable, TypeVar, Any, Dict
from functools import wraps
from playwright.async_api import async_playwright, Browser, BrowserContext, TimeoutError as PlaywrightTimeoutError
from src.infrastructure.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

T = TypeVar('T')

def retry_with_exponential_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    retry_on: tuple = (PlaywrightTimeoutError, ConnectionError, OSError)
):
    """
    Decorator that retries a function with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts (default: 3)
        base_delay: Initial delay in seconds (default: 1.0)
        retry_on: Tuple of exception types to retry on

    Retry pattern:
        - Attempt 1: No delay
        - Attempt 2: 1 second delay
        - Attempt 3: 2 second delay
        - Attempt 4: 4 second delay
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except retry_on as e:
                    last_exception = e

                    if attempt < max_retries:
                        # Exponential backoff: 2^attempt * base_delay
                        delay = (2 ** attempt) * base_delay
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} for {func.__name__} "
                            f"after {type(e).__name__}: {str(e)}. "
                            f"Waiting {delay}s before retry..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_retries} retries exhausted for {func.__name__}. "
                            f"Final error: {type(e).__name__}: {str(e)}"
                        )
                        raise

            # Should never reach here, but for type safety
            if last_exception:
                raise last_exception

        return wrapper
    return decorator

class PlaywrightScraperBase(ABC):
    """Base class for Playwright-based scrapers with rate limiting."""

    # Class-level tracking of last request time per source
    # Format: {"heritage": timestamp, "cng": timestamp, ...}
    _last_request_times: Dict[str, float] = {}

    def __init__(self, headless: bool = True, source: str = "default"):
        """
        Initialize the scraper.

        Args:
            headless: Whether to run browser in headless mode
            source: Source name for rate limiting (e.g., "heritage", "cng", "ebay")
        """
        self.headless = headless
        self.source = source.lower()
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None

    async def start(self):
        """Start the Playwright browser."""
        if self._playwright:
            return

        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=['--disable-blink-features=AutomationControlled', '--no-sandbox']
        )
        self._context = await self._browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        )

    async def stop(self):
        """Stop the browser."""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if self._playwright:
            await self._playwright.stop()
        self._playwright = None

    async def ensure_browser(self) -> bool:
        """
        Ensure browser is started. Returns True if successful.
        
        This method should be called before any scraping operation
        to ensure the browser and context are initialized.
        """
        try:
            if not self._browser or not self._context:
                await self.start()
            return True
        except Exception as e:
            logger.error(f"Failed to ensure browser: {e}")
            return False

    @property
    def context(self) -> Optional[BrowserContext]:
        """Public accessor for browser context."""
        return self._context

    async def _enforce_rate_limit(self):
        """
        Enforce rate limiting before making a request.

        Uses per-source rate limits from configuration.
        Sleeps if necessary to respect the minimum time between requests.
        """
        # Get rate limit for this source (or use default)
        rate_limit = settings.SCRAPER_RATE_LIMITS.get(
            self.source,
            settings.SCRAPER_RATE_LIMITS.get("default", 2.0)
        )

        # Check last request time for this source
        last_request = self._last_request_times.get(self.source, 0)
        current_time = time.time()
        time_since_last_request = current_time - last_request

        # If we need to wait, do so
        if time_since_last_request < rate_limit:
            wait_time = rate_limit - time_since_last_request
            logger.debug(
                f"Rate limiting {self.source}: waiting {wait_time:.2f}s "
                f"(limit: {rate_limit}s between requests)"
            )
            await asyncio.sleep(wait_time)

        # Update last request time for this source
        self._last_request_times[self.source] = time.time()

    @retry_with_exponential_backoff(max_retries=3, base_delay=1.0)
    async def fetch_page(self, url: str, wait_selector: str = None) -> str:
        """
        Fetch a page and return its HTML content.

        Features:
        - Automatic rate limiting per source (respects configured delays)
        - Automatic retries on transient errors (timeout, connection issues)
        - Exponential backoff: 1s, 2s, 4s (max 3 retries)

        Args:
            url: The URL to fetch
            wait_selector: Optional CSS selector to wait for before returning content

        Returns:
            HTML content of the page
        """
        # Enforce rate limiting before making request
        await self._enforce_rate_limit()

        if not self._context:
            await self.start()

        page = await self._context.new_page()
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=45000)
            if wait_selector:
                try:
                    await page.wait_for_selector(wait_selector, timeout=10000)
                except PlaywrightTimeoutError:
                    logger.warning(f"Timeout waiting for selector {wait_selector} on {url}")

            content = await page.content()
            return content
        finally:
            await page.close()
