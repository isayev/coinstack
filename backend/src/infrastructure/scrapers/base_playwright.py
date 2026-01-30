import asyncio
import logging
import time
import random
from abc import ABC
from typing import Optional, Callable, TypeVar, Dict, List
from functools import wraps
from playwright.async_api import async_playwright, Browser, BrowserContext, TimeoutError as PlaywrightTimeoutError
from src.infrastructure.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

T = TypeVar('T')

# Common User Agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36 Edg/119.0.0.0"
]

def retry_with_exponential_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    retry_on: tuple = (PlaywrightTimeoutError, ConnectionError, OSError)
):
    """
    Decorator that retries a function with exponential backoff.
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
                        delay = (2 ** attempt) * base_delay + random.uniform(0, 0.5) # Add jitter
                        logger.warning(
                            f"Retry {attempt + 1}/{max_retries} for {func.__name__} "
                            f"after {type(e).__name__}: {str(e)}. "
                            f"Waiting {delay:.2f}s before retry..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_retries} retries exhausted for {func.__name__}. "
                            f"Final error: {type(e).__name__}: {str(e)}"
                        )
                        raise

            if last_exception:
                raise last_exception

        return wrapper
    return decorator

class PlaywrightScraperBase(ABC):
    """Base class for Playwright-based scrapers with rate limiting and anti-bot measures."""

    # Class-level tracking of last request time per source
    _last_request_times: Dict[str, float] = {}

    def __init__(self, headless: bool = True, source: str = "default"):
        self.headless = headless
        self.source = source.lower()
        self._playwright = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None

    async def start(self):
        """Start the Playwright browser with stealth configurations."""
        if self._playwright:
            return

        self._playwright = await async_playwright().start()
        
        # Launch options for stealth
        launch_args = [
            '--disable-blink-features=AutomationControlled',
            '--no-sandbox',
            '--disable-infobars',
            '--disable-dev-shm-usage',
            '--disable-browser-side-navigation',
            '--disable-features=VizDisplayCompositor',
        ]
        
        self._browser = await self._playwright.chromium.launch(
            headless=self.headless,
            args=launch_args
        )
        
        # Rotate UA
        user_agent = random.choice(USER_AGENTS)
        
        self._context = await self._browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent=user_agent,
            locale='en-US',
            timezone_id='America/New_York',
            # basic permissions to look more real
            permissions=['geolocation'],
            geolocation={'latitude': 40.7128, 'longitude': -74.0060},
        )
        
        # Inject stealth scripts to mask webdriver
        await self._context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        """)

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
        """Ensure browser is started."""
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
        """Enforce rate limiting with jitter."""
        rate_limit = settings.SCRAPER_RATE_LIMITS.get(
            self.source,
            settings.SCRAPER_RATE_LIMITS.get("default", 2.0)
        )

        last_request = self._last_request_times.get(self.source, 0)
        current_time = time.time()
        time_since_last_request = current_time - last_request

        if time_since_last_request < rate_limit:
            wait_time = rate_limit - time_since_last_request
            # Add random jitter (0.1s to 0.5s) to look organic
            wait_time += random.uniform(0.1, 0.5)
            
            logger.debug(
                f"Rate limiting {self.source}: waiting {wait_time:.2f}s"
            )
            await asyncio.sleep(wait_time)

        self._last_request_times[self.source] = time.time()

    @retry_with_exponential_backoff(max_retries=3, base_delay=1.0)
    async def fetch_page(self, url: str, wait_selector: str = None) -> str:
        """Fetch a page and return its HTML content."""
        await self._enforce_rate_limit()

        if not self._context:
            await self.start()

        page = await self._context.new_page()
        try:
            # Set extra headers
            await page.set_extra_http_headers({
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            })
            
            response = await page.goto(url, wait_until='domcontentloaded', timeout=45000)
            
            if not response:
                raise ConnectionError("No response received")
                
            if response.status >= 400:
                # Specific check for 403/429 which usually means blocked
                if response.status in (403, 429):
                    logger.warning(f"Likely blocked by {self.source} (HTTP {response.status})")
                
            if wait_selector:
                try:
                    await page.wait_for_selector(wait_selector, timeout=10000)
                except PlaywrightTimeoutError:
                    logger.warning(f"Timeout waiting for selector {wait_selector} on {url}")

            content = await page.content()
            return content
        finally:
            await page.close()