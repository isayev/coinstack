import logging
import re
import asyncio
from typing import Optional, List, Dict, Any
from playwright.async_api import async_playwright, Page, Browser, BrowserContext

logger = logging.getLogger(__name__)

from app.services.scrapers.base import BaseScraper, ScraperResult, LotData
from app.models.coin import Coin

class BrowserScraper(BaseScraper):
    """Base class for Playwright-based scrapers."""
    
    def __init__(self, timeout: float = 30.0):
        super().__init__()
        self.timeout = timeout * 1000  # Convert to ms
        
    async def scrape_page(self, url: str) -> ScraperResult:
        """Scrape a page using Playwright."""
        async with async_playwright() as p:
            # Launch browser
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            )
            page = await context.new_page()
            
            try:
                # Go to URL
                logger.info(f"Navigating to {url}")
                await page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")
                
                # Parse content
                data = await self.extract_data(page)
                
                if not data:
                    return ScraperResult(
                        success=False,
                        status="error",
                        error_message="Failed to extract data from page"
                    )
                
                # Map to standard result
                lot_data = self.map_to_lot_data(data, url)
                
                return ScraperResult(
                    success=True,
                    status="success",
                    lot_data=lot_data,
                    raw_data=data
                )
                
            except Exception as e:
                logger.exception(f"Error scraping {url}")
                return ScraperResult(
                    success=False,
                    status="error",
                    error_message=str(e)
                )
                
            finally:
                await browser.close()

    async def extract_data(self, page: Page) -> Dict[str, Any]:
        """Extract raw data from page. Override in subclasses."""
        raise NotImplementedError

    def map_to_lot_data(self, data: Dict[str, Any], url: str) -> LotData:
        """Map raw data to LotData. Override in subclasses."""
        raise NotImplementedError


class HeritagePageParser(BrowserScraper):
    """Scraper for Heritage Auctions (ha.com) coin pages."""
    
    async def extract_data(self, page: Page) -> Dict[str, Any]:
        data = {}
        
        # Check if valid lot page
        title_elem = await page.query_selector("h1.product-title")
        if not title_elem:
            logger.warning("No product title found, might not be a lot page")
            return {}
            
        data['title'] = await title_elem.inner_text()
        
        # Get description
        desc_elem = await page.query_selector(".lot-description")
        if desc_elem:
            data['description'] = await desc_elem.inner_text()
            
        # Get images
        # Heritage uses a carousel or main image
        # Try to find high-res links
        images = []
        img_elems = await page.query_selector_all(".carousel-inner img")
        if not img_elems:
            # Try main image
            img_elems = await page.query_selector_all("#main-image-container img")
            
        for img in img_elems:
            src = await img.get_attribute("src")
            if src:
                # Heritage thumbnails often have ?max_width=proxied, strip that for full size
                clean_src = src.split("?")[0]
                if clean_src not in images:
                    images.append(clean_src)
        
        data['images'] = images
        
        # Parse product details table
        # There's usually a "Product Details" section
        details_rows = await page.query_selector_all(".product-details-table tr")
        for row in details_rows:
            cols = await row.query_selector_all("td")
            if len(cols) == 2:
                key = (await cols[0].inner_text()).strip().rstrip(":")
                val = (await cols[1].inner_text()).strip()
                data[key] = val
                
        # Parse basic auction info from header or sidebar
        # Lot number
        lot_elem = await page.query_selector(".lot-number")
        if lot_elem:
             data['lot_number'] = (await lot_elem.inner_text()).replace("Lot", "").strip()
             
        # Prices
        prices = await page.inner_text(".price-container") if await page.query_selector(".price-container") else ""
        data['price_text'] = prices
        
        # Parse URL slug for quick info (often contains reign/date)
        # e.g. ...augustus-27-bc-ad-14...
        data['url_slug'] = page.url.split("/")[-1]
        
        return data

    def map_to_lot_data(self, data: Dict[str, Any], url: str) -> LotData:
        # Extract fields
        
        # Clean Description
        desc = data.get('description', '')
        
        # Parse price
        price = None
        # Try to find "Sold for: $1,200.00" pattern
        price_text = data.get('price_text', '')
        price_match = re.search(r'\$([\d,]+\.?\d*)', price_text)
        if price_match:
            price = float(price_match.group(1).replace(",", ""))
            
        # Parse Url Slug for Date/Ruler hints if description is sparse
        slug = data.get('url_slug', '')
        # Example: ...augustus-27-bc-ad-14...
        
        # Extract reign dates (AD xxx-xxx or BC xxx-xxx)
        dates_match = re.search(r'(ad|bc)-(\d+)-(\d+)', slug, re.I)
        if dates_match:
            era = dates_match.group(1).upper()
            start = dates_match.group(2)
            end = dates_match.group(3)
            # Standardize output: "AD 69-79" or "27-14 BC" (suffix format for BC is safer)
            if era == "BC":
                data['reign_dates'] = f"{start}-{end} {era}"
            else:
                data['reign_dates'] = f"{era} {start}-{end}"
        else:
            # Single date
            dates_match = re.search(r'(ad|bc)-(\d+)', slug, re.I)
            if dates_match:
                era = dates_match.group(1).upper()
                year = dates_match.group(2)
                if era == "BC":
                    data['reign_dates'] = f"{year} {era}"
                else:
                    data['reign_dates'] = f"{era} {year}"
        
        # Extract denomination
        denom_patterns = [
            r'Denarius', r'Aureus', r'Sestertius', r'Dupondius', r'As', r'Semis', r'Quadrans',
            r'Tetradrachm', r'Drachm', r'Stater', r'Shekel', r'Solidus', r'Siliqua', r'Follis'
        ]
        denomination = None
        for pat in denom_patterns:
            if re.search(pat, desc, re.I) or re.search(pat, data.get('title', ''), re.I):
                denomination = pat
                break
                
        return LotData(
            lot_id=data.get('lot_number', 'Unknown'),
            house="Heritage",
            url=url,
            title=data.get('title', ''),
            description=desc,
            currency="USD",
            hammer_price=price, # Heritage shows total usually
            total_price=price,
            sold=True if price else False,
            auction_date=None, # Need to parse form listing
            estimate_low=None,
            estimate_high=None,
            buyer_premium=None,
            lot_number=data.get('lot_number'),
            sale_name="Heritage Auction",
            photos=data.get('images', []),
            
            # Mapped fields
            denomination=denomination,
            reign_dates=data.get('reign_dates')
        )
