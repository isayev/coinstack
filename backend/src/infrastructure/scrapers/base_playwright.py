import asyncio
import logging
from abc import ABC, abstractmethod
from typing import Optional
from playwright.async_api import async_playwright, Browser, BrowserContext

logger = logging.getLogger(__name__)

class PlaywrightScraperBase(ABC):
    """Base class for Playwright-based scrapers."""
    
    def __init__(self, headless: bool = True):
        self.headless = headless
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

    async def fetch_page(self, url: str, wait_selector: str = None) -> str:
        """Fetch a page and return its HTML content."""
        if not self._context:
            await self.start()
        
        page = await self._context.new_page()
        try:
            await page.goto(url, wait_until='domcontentloaded', timeout=45000)
            if wait_selector:
                try:
                    await page.wait_for_selector(wait_selector, timeout=10000)
                except Exception:
                    logger.warning(f"Timeout waiting for selector {wait_selector} on {url}")
            
            content = await page.content()
            return content
        finally:
            await page.close()
