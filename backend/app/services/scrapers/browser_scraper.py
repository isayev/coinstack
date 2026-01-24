"""Browser-based scraper using Playwright with stealth mode.

Uses real browser automation to bypass bot detection for infrequent scraping.
Designed for low-volume, high-reliability extraction from auction sites.
"""
import asyncio
import random
import logging
from typing import Optional
from dataclasses import dataclass
from datetime import datetime
from contextlib import asynccontextmanager

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

# Try to import stealth - may use different APIs in different versions
try:
    from playwright_stealth.stealth import Stealth
    HAS_STEALTH = True
except ImportError:
    HAS_STEALTH = False
    Stealth = None

logger = logging.getLogger(__name__)


@dataclass
class BrowserConfig:
    """Configuration for browser-based scraping."""
    headless: bool = True
    slow_mo: int = 50  # Milliseconds between actions
    viewport_width: int = 1920
    viewport_height: int = 1080
    # Random delays to appear human-like
    min_delay: float = 1.0
    max_delay: float = 3.0
    # Timeout for page loads
    timeout: int = 30000
    # User agent rotation
    user_agents: list[str] = None
    
    def __post_init__(self):
        if self.user_agents is None:
            self.user_agents = [
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
            ]


class BrowserScraper:
    """Browser-based scraper with stealth capabilities."""
    
    def __init__(self, config: Optional[BrowserConfig] = None):
        self.config = config or BrowserConfig()
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._playwright = None
    
    async def _random_delay(self):
        """Add random human-like delay."""
        delay = random.uniform(self.config.min_delay, self.config.max_delay)
        await asyncio.sleep(delay)
    
    async def _get_random_user_agent(self) -> str:
        """Get a random user agent."""
        return random.choice(self.config.user_agents)
    
    async def start(self):
        """Start the browser."""
        if self._browser is not None:
            return
            
        self._playwright = await async_playwright().start()
        
        # More aggressive anti-detection args
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-web-security',
            '--disable-features=IsolateOrigins,site-per-process',
            '--disable-site-isolation-trials',
            '--disable-features=BlockInsecurePrivateNetworkRequests',
            # Make it look more like a real browser
            '--enable-features=NetworkService,NetworkServiceInProcess',
            '--allow-running-insecure-content',
            '--disable-background-networking',
            '--disable-default-apps',
            '--disable-extensions',
            '--disable-sync',
            '--disable-translate',
            '--metrics-recording-only',
            '--mute-audio',
            '--no-first-run',
        ]
        
        self._browser = await self._playwright.chromium.launch(
            headless=self.config.headless,
            slow_mo=self.config.slow_mo,
            args=browser_args,
        )
        
        # Create context with realistic settings
        self._context = await self._browser.new_context(
            viewport={'width': self.config.viewport_width, 'height': self.config.viewport_height},
            user_agent=await self._get_random_user_agent(),
            locale='en-US',
            timezone_id='America/New_York',
            permissions=['geolocation'],
            java_script_enabled=True,
            # Add realistic device properties
            device_scale_factor=1,
            is_mobile=False,
            has_touch=False,
            # Bypass some detection
            bypass_csp=True,
            ignore_https_errors=True,
            # Extra headers to look more legitimate
            extra_http_headers={
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-User': '?1',
            }
        )
        
        # Inject scripts to mask automation
        await self._context.add_init_script("""
            // Remove webdriver property
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Mask plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                    { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                    { name: 'Native Client', filename: 'internal-nacl-plugin' },
                ],
            });
            
            // Mask languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            
            // Mask permissions
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Add Chrome runtime
            window.chrome = {
                runtime: {},
            };
        """)
        
        logger.info("Browser scraper started")
    
    async def stop(self):
        """Stop the browser."""
        if self._context:
            await self._context.close()
            self._context = None
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        logger.info("Browser scraper stopped")
    
    @asynccontextmanager
    async def new_page(self) -> Page:
        """Create a new page with stealth mode."""
        if self._context is None:
            await self.start()
        
        page = await self._context.new_page()
        
        # Apply stealth mode to avoid detection (if available)
        if HAS_STEALTH and Stealth:
            try:
                stealth = Stealth()
                await stealth.apply_stealth_async(page)
            except Exception as e:
                logger.warning(f"Could not apply stealth: {e}")
        
        # Set default timeout
        page.set_default_timeout(self.config.timeout)
        
        try:
            yield page
        finally:
            await page.close()
    
    async def fetch_page(self, url: str, retry_on_403: bool = True) -> tuple[str, str]:
        """
        Fetch a page and return its HTML content and final URL.
        
        Args:
            url: URL to fetch
            retry_on_403: If True, retry once on 403 with longer delays
        
        Returns:
            Tuple of (html_content, final_url)
        """
        async with self.new_page() as page:
            await self._random_delay()
            
            logger.info(f"Fetching: {url}")
            
            # First, go to a neutral page to establish cookies
            try:
                base_url = '/'.join(url.split('/')[:3])  # e.g., https://coins.ha.com
                await page.goto(base_url, wait_until='domcontentloaded', timeout=15000)
                await asyncio.sleep(random.uniform(1, 2))
            except Exception:
                pass  # Continue even if this fails
            
            response = await page.goto(url, wait_until='networkidle')
            
            if response is None:
                raise Exception(f"Failed to load page: {url}")
            
            if response.status == 403 and retry_on_403:
                # Wait longer and retry - sometimes sites need time to validate
                logger.info(f"Got 403, waiting and retrying: {url}")
                await asyncio.sleep(random.uniform(3, 5))
                
                # Simulate some human behavior
                await page.mouse.move(random.randint(100, 500), random.randint(100, 500))
                await asyncio.sleep(0.5)
                
                # Reload
                response = await page.reload(wait_until='networkidle')
            
            if response and response.status >= 400:
                # Even on error, try to get the content - sometimes the page still loads
                html = await page.content()
                if len(html) > 5000:  # If there's substantial content, use it
                    logger.warning(f"Got {response.status} but page has content, using anyway")
                    return html, page.url
                raise Exception(f"HTTP {response.status} for {url}")
            
            # Wait a bit for any dynamic content
            await self._random_delay()
            
            # Scroll down to trigger lazy loading
            await page.mouse.wheel(0, 500)
            await asyncio.sleep(0.5)
            
            # Get the HTML content
            html = await page.content()
            final_url = page.url
            
            return html, final_url


class HeritagePageParser:
    """Parse Heritage Auctions coin pages."""
    
    @staticmethod
    def parse_url_slug(url: str) -> dict:
        """
        Extract coin data from Heritage URL slug.
        
        Heritage URLs contain descriptive slugs like:
        roman-provincial-scythia-geto-dacians-coson-ca-after-54-bc-av-stater-18mm-853-gm-12h-ngc-choice-au-5-5-4-5
        
        This is useful when the page returns 403.
        """
        import re
        data = {}
        
        # Extract the slug from URL (between /itm/.../ and /a/)
        slug_match = re.search(r'/itm/[^/]+/[^/]+/([^/]+)/a/', url)
        if not slug_match:
            return data
        
        slug = slug_match.group(1)
        
        # Convert slug to title-like text
        title = slug.replace('-', ' ').title()
        data['title'] = title
        
        # Lot number from URL
        lot_match = re.search(r'/a/(\d+)-(\d+)\.s', url)
        if lot_match:
            data['sale_id'] = lot_match.group(1)
            data['lot_number'] = lot_match.group(2)
        
        # Weight: Heritage uses "853-gm" for 8.53g or "330-gm" for 3.30g
        # Pattern: 3+ digits followed by -gm
        weight_match = re.search(r'-(\d)(\d{2})-gm', slug)
        if weight_match:
            data['weight_g'] = float(f"{weight_match.group(1)}.{weight_match.group(2)}")
        else:
            # Try 4-digit: "1053-gm" -> 10.53g
            weight_match = re.search(r'-(\d{2})(\d{2})-gm', slug)
            if weight_match:
                data['weight_g'] = float(f"{weight_match.group(1)}.{weight_match.group(2)}")
        
        # Diameter: "18mm" or "18-mm"
        diameter_match = re.search(r'-(\d+)mm', slug)
        if diameter_match:
            data['diameter_mm'] = float(diameter_match.group(1))
        
        # Die axis: "12h" at end or middle
        die_match = re.search(r'-(\d{1,2})h(?:-|$)', slug)
        if die_match:
            data['die_axis'] = int(die_match.group(1))
        
        # Grade - Heritage often includes NGC/PCGS grades
        # Patterns: "ngc-choice-au-5-5-4-5" or "ngc-ms-64" or "ngc-vf"
        grade_patterns = [
            # NGC with numeric grade and strike/surface: "ngc-choice-au-5-5-4-5"
            (r'ngc-([a-z]+-?[a-z]*-?\d*)-(\d)-(\d)-(\d)-(\d)', 
             lambda m: f"NGC {m.group(1).upper().replace('-', ' ')} {m.group(2)}/{m.group(3)} {m.group(4)}/{m.group(5)}"),
            # NGC with numeric: "ngc-ms-64"
            (r'ngc-([a-z]+)-(\d+)', lambda m: f"NGC {m.group(1).upper()} {m.group(2)}"),
            # NGC descriptive: "ngc-choice-au" or "ngc-vf"
            (r'ngc-([a-z]+-?[a-z]*)', lambda m: f"NGC {m.group(1).upper().replace('-', ' ')}"),
            # PCGS similar patterns
            (r'pcgs-([a-z]+)-(\d+)', lambda m: f"PCGS {m.group(1).upper()} {m.group(2)}"),
            (r'pcgs-([a-z]+-?[a-z]*)', lambda m: f"PCGS {m.group(1).upper().replace('-', ' ')}"),
            # Raw grades (not necessarily at end - could be followed by surface issues)
            (r'-(superb-ef|choice-ef|near-ef|ef|good-vf|choice-vf|near-vf|vf|fine|good|poor)(?:-|$)', 
             lambda m: m.group(1).upper().replace('-', ' ')),
        ]
        
        for pattern, formatter in grade_patterns:
            grade_match = re.search(pattern, slug, re.I)
            if grade_match:
                if callable(formatter):
                    data['grade'] = formatter(grade_match)
                else:
                    data['grade'] = formatter
                # Check for grading service
                if 'ngc' in slug.lower():
                    data['grade_service'] = 'NGC'
                elif 'pcgs' in slug.lower():
                    data['grade_service'] = 'PCGS'
                break
        
        # Metal from slug
        if '-ar-' in slug or 'denarius' in slug or 'drachm' in slug:
            data['metal'] = 'AR'  # Silver
        elif '-ae-' in slug or 'follis' in slug or 'as-' in slug:
            data['metal'] = 'AE'  # Bronze
        elif '-av-' in slug or 'aureus' in slug or 'stater' in slug:
            data['metal'] = 'AV'  # Gold
        elif '-bi-' in slug or 'antoninianus' in slug:
            data['metal'] = 'BI'  # Billon
        
        # Extract ruler from slug
        # Pattern: ruler name followed by "ad" dates or after category prefix
        # e.g., "roman-imperial-maximinus-i-ad-235-238" -> "Maximinus I"
        emperor_patterns = [
            r'(?:roman-(?:imperial|provincial|republic)-)?([a-z]+-(?:i{1,3}|ii|iii|iv|v|vi)?)(?:-ad-|-bc-|-ca-)',
            r'(?:roman-(?:imperial|provincial)-)?([a-z]+-the-[a-z]+)(?:-ad-|-bc-)',
            r'(?:roman-(?:imperial|provincial)-)?(?:thrace-[a-z]+-)?([a-z]+)(?:-ad-\d)',
        ]
        for pattern in emperor_patterns:
            ruler_match = re.search(pattern, slug, re.I)
            if ruler_match:
                ruler_raw = ruler_match.group(1)
                ruler = ruler_raw.replace('-', ' ').title()
                # Clean up Roman numerals
                ruler = ruler.replace(' I ', ' I').replace(' Ii ', ' II').replace(' Iii ', ' III')
                ruler = ruler.replace(' Iv ', ' IV').replace(' Vi ', ' VI')
                data['ruler'] = ruler
                break
        
        # Extract reign dates (AD xxx-xxx or BC xxx-xxx)
        dates_match = re.search(r'(ad|bc)-(\d+)-(\d+)', slug, re.I)
        if dates_match:
            era = dates_match.group(1).upper()
            start = dates_match.group(2)
            end = dates_match.group(3)
            data['reign_dates'] = f"{era} {start}-{end}"
        else:
            # Single date
            dates_match = re.search(r'(ad|bc)-(\d+)', slug, re.I)
            if dates_match:
                data['reign_dates'] = f"{dates_match.group(1).upper()} {dates_match.group(2)}"
        
        # Extract denomination
        denom_patterns = [
            (r'\b(stater)\b', 'Stater'),
            (r'\b(aureus)\b', 'Aureus'),
            (r'\b(solidus)\b', 'Solidus'),
            (r'\b(denarius)\b', 'Denarius'),
            (r'\b(antoninianus)\b', 'Antoninianus'),
            (r'\b(sestertius)\b', 'Sestertius'),
            (r'\b(dupondius)\b', 'Dupondius'),
            (r'-as-(?:\d|$)', 'As'),
            (r'\b(follis)\b', 'Follis'),
            (r'\b(drachm)\b', 'Drachm'),
            (r'\b(tetradrachm)\b', 'Tetradrachm'),
        ]
        for pattern, denom in denom_patterns:
            if re.search(pattern, slug, re.I):
                data['denomination'] = denom
                break
        
        # Extract category from URL
        category_match = re.search(r'/itm/([^/]+)/([^/]+)/', url)
        if category_match:
            data['category'] = category_match.group(1).replace('-', ' ').title()
            data['subcategory'] = category_match.group(2).replace('-', ' ').title()
        
        # Extract mint/region from slug (after category, before ruler)
        # e.g., "thrace-anchialus" in "roman-provincial-thrace-anchialus-maximinus"
        region_match = re.search(r'(?:roman-provincial-|greek-)?([a-z]+-[a-z]+)(?=-[a-z]+-(?:i{1,3}|ad|bc))', slug, re.I)
        if region_match:
            region = region_match.group(1).replace('-', ' ').title()
            if region not in ['Roman Imperial', 'Roman Provincial', 'Roman Republic']:
                data['mint'] = region
        
        # Surface issues from slug
        if 'altered-surface' in slug:
            data['surface_issues'] = 'Altered Surface'
        elif 'tooled' in slug:
            data['surface_issues'] = 'Tooled'
        elif 'scratches' in slug:
            data['surface_issues'] = 'Scratches'
        
        return data
    
    @staticmethod
    def parse(html: str, url: str) -> dict:
        """Parse Heritage auction page HTML."""
        from bs4 import BeautifulSoup
        import re
        
        soup = BeautifulSoup(html, 'lxml')
        data = {
            'url': url,
            'auction_house': 'Heritage',
            'scraped_at': datetime.utcnow().isoformat(),
        }
        
        # First get data from URL slug as fallback
        slug_data = HeritagePageParser.parse_url_slug(url)
        
        # Title - usually in h1 or specific div
        title_elem = soup.select_one('h1.lot-title, .lot-description h1, h1')
        if title_elem:
            data['title'] = title_elem.get_text(strip=True)
        
        # Lot number from URL or page
        lot_match = re.search(r'/a/(\d+)-(\d+)\.s', url)
        if lot_match:
            data['sale_id'] = lot_match.group(1)
            data['lot_number'] = lot_match.group(2)
        
        # Price - look for realized price
        price_selectors = [
            '.price-realized',
            '.realized-price',
            '[data-price]',
            '.lot-price',
        ]
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_match = re.search(r'\$?([\d,]+(?:\.\d{2})?)', price_text)
                if price_match:
                    data['hammer_price'] = float(price_match.group(1).replace(',', ''))
                    data['sold'] = True
                break
        
        # Description - contains coin details
        desc_selectors = [
            '.lot-description',
            '.description-text',
            '.item-description',
        ]
        for selector in desc_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                data['description'] = desc_elem.get_text(separator=' ', strip=True)
                break
        
        # Extract physical attributes from description
        desc_text = data.get('description', '') + ' ' + data.get('title', '')
        
        # Weight (e.g., "3.30 gm", "3.30g")
        weight_match = re.search(r'(\d+\.?\d*)\s*(?:gm|g(?:rams?)?)\b', desc_text, re.I)
        if weight_match:
            data['weight_g'] = float(weight_match.group(1))
        
        # Diameter (e.g., "17mm", "17 mm")
        diameter_match = re.search(r'(\d+\.?\d*)\s*mm\b', desc_text, re.I)
        if diameter_match:
            data['diameter_mm'] = float(diameter_match.group(1))
        
        # Die axis (e.g., "6h", "12h")
        die_match = re.search(r'(\d{1,2})h\b', desc_text)
        if die_match:
            data['die_axis'] = int(die_match.group(1))
        
        # Grade (look for NGC/PCGS grades or raw grades)
        grade_patterns = [
            r'NGC\s+([\w\s\+\-\*]+?)(?:\s|,|$)',
            r'PCGS\s+([\w\s\+\-\*]+?)(?:\s|,|$)',
            r'\b(MS|AU|XF|EF|VF|F|VG|G|AG|PR|PF)\s*[-]?\s*(\d{1,2})?\b',
            r'\b(Choice|Fine|Very Fine|Extremely Fine|About Uncirculated)\b',
        ]
        for pattern in grade_patterns:
            grade_match = re.search(pattern, desc_text, re.I)
            if grade_match:
                data['grade'] = grade_match.group(0).strip()
                if 'NGC' in desc_text:
                    data['grade_service'] = 'NGC'
                elif 'PCGS' in desc_text:
                    data['grade_service'] = 'PCGS'
                break
        
        # Images
        img_urls = []
        for img in soup.select('img[src*="coins"], img[src*="lot-image"], .lot-images img'):
            src = img.get('src') or img.get('data-src')
            if src and 'thumbnail' not in src.lower():
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = 'https://coins.ha.com' + src
                img_urls.append(src)
        
        if img_urls:
            data['photos'] = img_urls
            data['primary_photo_url'] = img_urls[0]
        
        # Merge with slug data - slug data fills in missing fields
        error_titles = [
            'Access Denied',
            '403 Forbidden',
            'Error',
            '404',
            'Not Found',
            'Page not found',
        ]
        
        for key, value in slug_data.items():
            current = data.get(key)
            
            # For title specifically, replace error messages with slug title
            if key == 'title':
                if current is None or current == '' or current in error_titles or 'forbidden' in str(current).lower():
                    data[key] = value
            # For other fields, only fill if empty
            elif current is None or current == '':
                data[key] = value
        
        return data


class CNGPageParser:
    """Parse CNG (Classical Numismatic Group) coin pages.
    
    Supports both old format (www.cngcoins.com/Coin.aspx?CoinID=...) 
    and new format (auctions.cngcoins.com/lots/view/...).
    """
    
    @staticmethod
    def parse_url_slug(url: str) -> dict:
        """
        Extract coin data from the URL slug.
        
        CNG URLs contain descriptive slugs like:
        titus-as-caesar-ad-69-79-ar-denarius-19mm-303-g-6h-rome-mint-struck-under-vespasian-ad-75-vf
        
        This is a reliable fallback when JS doesn't render.
        """
        import re
        data = {}
        
        # Extract the slug from URL
        slug_match = re.search(r'/lots/view/[^/]+/(.+?)(?:\?|$)', url)
        if not slug_match:
            return data
        
        slug = slug_match.group(1)
        
        # Convert slug to title-like text
        title = slug.replace('-', ' ').title()
        data['title'] = title
        
        # Extract physical details from slug
        # Weight patterns in CNG slugs (separated by hyphens):
        # "-303-g-" -> 3.03g (3 digits = X.XX, common for ancient coins)
        # "-3-03-g-" -> 3.03g (explicit decimal with hyphen)
        # "-10-5-g-" -> 10.5g  
        # "-3-g-" -> 3g (whole number, rare)
        
        # Pattern 1: Explicit decimal "X-XX-g" like "-3-03-g-" 
        weight_match = re.search(r'-(\d+)-(\d+)-g(?:-|$)', slug)
        if weight_match:
            data['weight_g'] = float(f"{weight_match.group(1)}.{weight_match.group(2)}")
        else:
            # Pattern 2: 3-digit compact format "-XXX-g-" like "-303-g-" -> 3.03
            weight_match = re.search(r'-(\d)(\d{2})-g(?:-|$)', slug)
            if weight_match:
                data['weight_g'] = float(f"{weight_match.group(1)}.{weight_match.group(2)}")
            else:
                # Pattern 3: 4-digit compact format "-XXXX-g-" like "-1050-g-" -> 10.50
                weight_match = re.search(r'-(\d{2})(\d{2})-g(?:-|$)', slug)
                if weight_match:
                    data['weight_g'] = float(f"{weight_match.group(1)}.{weight_match.group(2)}")
                else:
                    # Pattern 4: Single/double digit whole number "-X-g-" or "-XX-g-"
                    weight_match = re.search(r'-(\d{1,2})-g(?:-|$)', slug)
                    if weight_match:
                        data['weight_g'] = float(weight_match.group(1))
        
        # Diameter: "19mm" or "19-mm"
        diameter_match = re.search(r'(\d+)-?mm\b', slug)
        if diameter_match:
            data['diameter_mm'] = float(diameter_match.group(1))
        
        # Die axis: "6h" or "6-h"
        die_match = re.search(r'(\d{1,2})-?h\b', slug)
        if die_match:
            data['die_axis'] = int(die_match.group(1))
        
        # Grade at end: "-vf", "-ef", "-choice-vf", "-good-vf"
        grade_patterns = [
            (r'-superb-ef$', 'Superb EF'),
            (r'-choice-ef$', 'Choice EF'),
            (r'-near-ef$', 'Near EF'),
            (r'-good-vf$', 'Good VF'),
            (r'-choice-vf$', 'Choice VF'),
            (r'-ef$', 'EF'),
            (r'-vf$', 'VF'),
            (r'-fine$', 'Fine'),
            (r'-f$', 'F'),
        ]
        for pattern, grade in grade_patterns:
            if re.search(pattern, slug, re.I):
                data['grade'] = grade
                break
        
        # Denomination from slug
        denom_patterns = [
            (r'\b(denarius)\b', 'Denarius'),
            (r'\b(antoninianus)\b', 'Antoninianus'),
            (r'\b(sestertius)\b', 'Sestertius'),
            (r'\b(aureus)\b', 'Aureus'),
            (r'\b(solidus)\b', 'Solidus'),
            (r'\b(follis)\b', 'Follis'),
            (r'\b(as|dupondius|quadrans)\b', lambda m: m.group(1).title()),
        ]
        for pattern, denom in denom_patterns:
            if re.search(pattern, slug, re.I):
                data['denomination'] = denom if isinstance(denom, str) else denom(re.search(pattern, slug, re.I))
                break
        
        # Metal from slug
        if '-ar-' in slug or slug.startswith('ar-'):
            data['metal'] = 'AR'  # Silver
        elif '-ae-' in slug or slug.startswith('ae-'):
            data['metal'] = 'AE'  # Bronze
        elif '-av-' in slug or slug.startswith('av-'):
            data['metal'] = 'AV'  # Gold
        
        return data
    
    @staticmethod
    def parse(html: str, url: str) -> dict:
        """Parse CNG auction page HTML."""
        from bs4 import BeautifulSoup
        import re
        
        soup = BeautifulSoup(html, 'lxml')
        data = {
            'url': url,
            'auction_house': 'CNG',
            'scraped_at': datetime.utcnow().isoformat(),
        }
        
        # First, try to extract from URL slug (reliable fallback)
        slug_data = CNGPageParser.parse_url_slug(url)
        
        # Lot ID from URL - handle both old and new formats
        # New format: auctions.cngcoins.com/lots/view/4-I2GBGT/slug
        new_lot_match = re.search(r'/lots/view/([^/]+)', url)
        if new_lot_match:
            data['lot_number'] = new_lot_match.group(1)
        else:
            # Old format: CoinID=123456
            old_match = re.search(r'CoinID=(\d+)', url)
            if old_match:
                data['lot_number'] = old_match.group(1)
        
        # Title - try multiple selectors for the new Auction Mobility platform
        title_selectors = [
            'h1',  # Main title
            '.lot-title',
            '[class*="title"]',
            'title',  # Fallback to page title
        ]
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                # Clean up title - remove site name suffix
                title_text = re.sub(r'\s*\|\s*Classical Numismatic Group.*$', '', title_text)
                if title_text and len(title_text) > 10:
                    data['title'] = title_text
                    break
        
        # For JS-heavy pages, try to extract from page title tag
        if not data.get('title'):
            title_tag = soup.find('title')
            if title_tag:
                title_text = title_tag.get_text(strip=True)
                # Parse "Titus. As Caesar... | Classical Numismatic Group"
                title_text = re.sub(r'\s*\|\s*Classical Numismatic Group.*$', '', title_text)
                if title_text:
                    data['title'] = title_text
        
        # Extract physical details from title (common CNG format)
        # e.g., "AR Denarius (19mm, 3.03 g, 6h)"
        title_text = data.get('title', '')
        
        # Weight from title - format: "3.03 g" or "3.03g"
        weight_match = re.search(r'(\d+\.?\d*)\s*g(?:m|rams?)?\b', title_text, re.I)
        if weight_match:
            data['weight_g'] = float(weight_match.group(1))
        
        # Diameter from title - format: "19mm"
        diameter_match = re.search(r'(\d+\.?\d*)\s*mm\b', title_text, re.I)
        if diameter_match:
            data['diameter_mm'] = float(diameter_match.group(1))
        
        # Die axis from title - format: "6h"
        die_match = re.search(r'(\d{1,2})h\b', title_text)
        if die_match:
            data['die_axis'] = int(die_match.group(1))
        
        # Grade from title - at end like "VF", "EF", "Choice VF"
        grade_patterns = [
            r'\.\s*(Superb EF|Choice EF|Near EF|EF|Good VF|Choice VF|VF|Fine|Good|Fair)\s*\.?\s*$',
            r'\.\s*(MS|AU|XF|EF|VF|F|VG|G)\s*[-]?\s*(\d{1,2})?\s*\.?\s*$',
        ]
        for pattern in grade_patterns:
            grade_match = re.search(pattern, title_text, re.I)
            if grade_match:
                data['grade'] = grade_match.group(1).strip()
                break
        
        # Description - look for lot description content
        desc_selectors = [
            '.lot-description',
            '.description',
            '[class*="description"]',
            '#lotDescription',
        ]
        for selector in desc_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                desc_text = desc_elem.get_text(separator=' ', strip=True)
                if len(desc_text) > 20:
                    data['description'] = desc_text
                    break
        
        # Images - look for lot images
        img_urls = []
        img_selectors = [
            'img[src*="cloudfront"]',  # AWS CloudFront CDN
            'img[src*="cng"]',
            '.lot-image img',
            '[class*="image"] img',
        ]
        for selector in img_selectors:
            for img in soup.select(selector):
                src = img.get('src') or img.get('data-src')
                if src and 'placeholder' not in src.lower():
                    if src.startswith('//'):
                        src = 'https:' + src
                    elif src.startswith('/'):
                        src = 'https://auctions.cngcoins.com' + src
                    if src not in img_urls:
                        img_urls.append(src)
        
        if img_urls:
            data['photos'] = img_urls
            data['primary_photo_url'] = img_urls[0]
        
        # Reference numbers from description or title
        full_text = data.get('description', '') + ' ' + title_text
        ref_patterns = [
            r'RIC\s+(?:[\w]+\s+)?(\d+\w*)',
            r'RPC\s+(?:[\w]+\s+)?(\d+\w*)',
            r'RSC\s+(\d+\w*)',
            r'Sear\s+(\d+\w*)',
            r'Crawford\s+(\d+/\d+)',
        ]
        references = []
        for pattern in ref_patterns:
            for match in re.finditer(pattern, full_text, re.I):
                references.append(match.group(0).strip())
        if references:
            data['references'] = references
        
        # Merge with slug data - slug data fills in missing fields
        error_titles = [
            'Oh no, something went wrong',
            'Error',
            '404',
            'Not Found',
            'Page not found',
        ]
        
        for key, value in slug_data.items():
            current = data.get(key)
            
            # For title specifically, replace error messages with slug title
            if key == 'title':
                if current is None or current == '' or current in error_titles or 'something went wrong' in str(current).lower():
                    data[key] = value
            # For other fields, only fill if empty
            elif current is None or current == '':
                data[key] = value
        
        return data


async def scrape_heritage(
    url: str, 
    config: Optional[BrowserConfig] = None,
    captcha_wait: float = 0.0
) -> dict:
    """Scrape a Heritage Auctions coin page with comprehensive metadata extraction.
    
    Uses the rich Heritage parser package with STRICT rate limiting:
    - 3 second minimum between requests
    - 429 errors trigger 60s backoff
    - 403 = IP blocked (wait 24 hours)
    
    Heritage is aggressive about bot detection. Be respectful.
    
    Args:
        url: Heritage auction URL
        config: Browser configuration (headless=False for visible browser)
        captcha_wait: Extra seconds to wait for manual captcha solving (campaign mode)
    """
    from app.services.scrapers.heritage_rich.parser import HeritageParser
    from app.services.scrapers.heritage_rich.scraper import heritage_data_to_dict, HeritageRateLimitError, HeritageBlockedError
    
    scraper = BrowserScraper(config)
    heritage_parser = HeritageParser()
    
    # For campaign mode (headless=False), use longer delays
    is_campaign_mode = config and not config.headless
    
    # STRICT rate limiting for Heritage - 3 second minimum (longer for campaign)
    base_delay = 5.0 if is_campaign_mode else 3.0
    await asyncio.sleep(base_delay)
    
    try:
        await scraper.start()
        
        async with scraper.new_page() as page:
            # Additional random delay for Heritage
            delay_range = (3.0, 5.0) if is_campaign_mode else (1.0, 2.0)
            await asyncio.sleep(random.uniform(*delay_range))
            
            logger.info(f"Fetching Heritage: {url}" + (" [CAMPAIGN MODE]" if is_campaign_mode else ""))
            
            # Establish a proper session first - browse like a human
            try:
                # Visit main domain first
                await page.goto('https://www.ha.com', wait_until='networkidle', timeout=30000)
                await asyncio.sleep(3 if is_campaign_mode else 2)
                
                # Then visit coins section
                await page.goto('https://coins.ha.com', wait_until='networkidle', timeout=30000)
                await asyncio.sleep(3 if is_campaign_mode else 2)
                
                # Scroll a bit to simulate human behavior
                await page.evaluate('window.scrollTo(0, 300)')
                await asyncio.sleep(2 if is_campaign_mode else 1)
            except Exception as e:
                logger.warning(f"Session warmup failed: {e}")
            
            # Now fetch the actual lot page
            response = await page.goto(url, wait_until='networkidle', timeout=60000)
            
            # Check for rate limiting / blocking
            if response:
                status = response.status
                
                if status == 429:
                    logger.error("Heritage 429 Rate Limited! Waiting 60s...")
                    await asyncio.sleep(60)
                    raise HeritageRateLimitError("429 Rate Limited")
                
                if status == 403:
                    logger.error("Heritage 403 BLOCKED! IP may need 24 hour cooldown.")
                    # Still try to get data from URL slug
                    slug_data = HeritagePageParser.parse_url_slug(url)
                    slug_data['auction_house'] = 'Heritage Auctions'
                    slug_data['_error'] = '403 Blocked - data from URL slug only'
                    slug_data['scraped_at'] = datetime.utcnow().isoformat()
                    return slug_data
            
            # CAMPAIGN MODE: Wait for manual captcha solving
            # User sees the browser and can interact with it
            if captcha_wait > 0:
                logger.info(f"Waiting {captcha_wait}s for manual captcha solving...")
                await asyncio.sleep(captcha_wait)
            
            # Wait for content
            await asyncio.sleep(3 if is_campaign_mode else 2)
            
            try:
                await page.wait_for_selector('h1, .lot-title, #auction-description', timeout=30000)
            except:
                logger.warning("Timeout waiting for Heritage page content")
            
            html = await page.content()
            
            # Use the rich Heritage parser
            try:
                coin_data = heritage_parser.parse(html, url)
                
                # Try to extract additional data via JS
                js_data = await page.evaluate('''() => {
                    const result = {};
                    
                    // Price
                    const priceEl = document.querySelector('.price-sold, .bid-price, [class*="Price"]');
                    if (priceEl) {
                        const match = priceEl.innerText.match(/\\$([\\d,]+)/);
                        if (match) result.sold_price = parseInt(match[1].replace(',', ''));
                    }
                    
                    // Images
                    result.images = [];
                    document.querySelectorAll('img').forEach(img => {
                        let src = img.src || img.getAttribute('data-src');
                        if (src && (src.includes('heritagestatic') || src.includes('cloudfront'))) {
                            if (!src.includes('logo') && !src.includes('icon')) {
                                src = src.replace('/thumb/', '/').replace('/sm/', '/lg/');
                                if (!result.images.includes(src)) {
                                    result.images.push(src);
                                }
                            }
                        }
                    });
                    
                    // NGC cert link
                    const ngcLink = document.querySelector('a[href*="ngccoin.com/certlookup"]');
                    if (ngcLink) {
                        result.ngc_cert_url = ngcLink.href;
                        const certMatch = ngcLink.href.match(/certlookup\\/(\\d+)/);
                        if (certMatch) result.ngc_cert_number = certMatch[1];
                    }
                    
                    result.is_sold = !!document.querySelector('.sold, [class*="sold"]');
                    
                    return result;
                }''')
                
                # Update with JS data
                if coin_data.auction and js_data.get('sold_price'):
                    if not coin_data.auction.sold_price_usd:
                        coin_data.auction.sold_price_usd = js_data['sold_price']
                
                if js_data.get('ngc_cert_number') and coin_data.slab_grade:
                    if not coin_data.slab_grade.certification_number:
                        coin_data.slab_grade.certification_number = js_data['ngc_cert_number']
                
                # Add images from JS
                if js_data.get('images'):
                    from app.services.scrapers.heritage_rich.models import HeritageImage
                    existing_urls = {img.url for img in coin_data.images}
                    for i, img_url in enumerate(js_data['images']):
                        if img_url not in existing_urls:
                            coin_data.images.append(HeritageImage(
                                url=img_url,
                                url_full_res=img_url,
                                index=len(coin_data.images),
                                image_type="coin",
                                source="heritage"
                            ))
                
                # Convert to dict format for API
                data = heritage_data_to_dict(coin_data)
                return data
                
            except Exception as e:
                logger.warning(f"Error with Heritage parser: {e}, falling back to basic extraction")
                
                # Fallback to old slug parser
                data = HeritagePageParser.parse(html, url)
                
                # Try to get images
                img_urls = []
                try:
                    img_urls = await page.evaluate('''() => {
                        const images = [];
                        document.querySelectorAll('img').forEach(img => {
                            const src = img.src || img.getAttribute('data-src');
                            if (src && (src.includes('heritagestatic') || src.includes('cloudfront'))) {
                                if (!src.includes('logo') && !src.includes('icon')) {
                                    images.push(src);
                                }
                            }
                        });
                        return [...new Set(images)];
                    }''')
                except:
                    pass
                
                if img_urls and not data.get('photos'):
                    data['photos'] = img_urls[:5]
                    data['primary_photo_url'] = img_urls[0] if img_urls else None
                
                return data
    
    finally:
        await scraper.stop()


async def scrape_cng(url: str, config: Optional[BrowserConfig] = None) -> dict:
    """Scrape a CNG coin page with full metadata extraction.
    
    Uses JSON-LD schema.org data embedded in CNG pages for comprehensive
    metadata extraction including ruler, provenance, references, etc.
    """
    # Import the new CNG parser
    from app.services.scrapers.cng.parser import CNGParser
    
    scraper = BrowserScraper(config)
    cng_parser = CNGParser()
    
    try:
        await scraper.start()
        
        async with scraper.new_page() as page:
            await scraper._random_delay()
            
            logger.info(f"Fetching CNG: {url}")
            await page.goto(url, wait_until='domcontentloaded')
            
            # Wait for Angular to render
            try:
                await page.wait_for_selector('h1, .lot-title, [class*="title"]', timeout=15000)
                await asyncio.sleep(2)
            except Exception as e:
                logger.warning(f"Timeout waiting for CNG page to render: {e}")
            
            # Get content after JS rendering
            html = await page.content()
            
            # Use the new CNG parser for JSON-LD extraction
            try:
                coin_data = cng_parser.parse(html, page.url)
                
                # Convert CNGCoinData to dict format expected by the API
                data = {
                    'url': coin_data.url,
                    'auction_house': 'CNG',
                    'lot_id': coin_data.cng_lot_id,
                    'title': coin_data.title,
                    'scraped_at': coin_data.scraped_at.isoformat(),
                    
                    # Ruler and classification
                    'ruler': coin_data.ruler,
                    'ruler_title': coin_data.ruler_title,
                    'reign_dates': coin_data.reign_dates,
                    'denomination': coin_data.denomination,
                    'metal': coin_data.metal.value if coin_data.metal else None,
                    'mint': coin_data.mint,
                    'struck_dates': coin_data.struck_dates,
                    'struck_under': coin_data.struck_under,
                    
                    # Physical measurements
                    'diameter_mm': coin_data.physical.diameter_mm,
                    'weight_g': coin_data.physical.weight_g,
                    'die_axis': coin_data.physical.die_axis_hours,
                    
                    # Descriptions
                    'obverse_description': coin_data.obverse_description,
                    'reverse_description': coin_data.reverse_description,
                    'description': coin_data.raw_description,
                    
                    # Condition
                    'grade': coin_data.grade,
                    'condition_notes': coin_data.condition_notes,
                    
                    # References - list of normalized refs
                    'references': [ref.normalized for ref in coin_data.references],
                    'references_raw': [ref.raw_text for ref in coin_data.references],
                    
                    # Provenance
                    'provenance': coin_data.provenance.raw_text if coin_data.provenance else None,
                    'pedigree_year': coin_data.provenance.pedigree_year if coin_data.provenance else None,
                    'has_provenance': coin_data.has_provenance,
                    
                    # Categories
                    'categories': coin_data.categories,
                    
                    # Images - get URLs from CNGImage objects
                    'photos': [img.url_full_res or img.url for img in coin_data.images],
                    'primary_photo_url': coin_data.images[0].url if coin_data.images else None,
                }
                
                # Auction info
                if coin_data.auction:
                    data['auction_name'] = coin_data.auction.auction_name
                    data['lot_number'] = coin_data.auction.lot_number
                    data['estimate_usd'] = coin_data.auction.estimate_usd
                    data['hammer_price'] = coin_data.auction.sold_price_usd
                    data['total_price_usd'] = coin_data.total_price_usd
                    data['is_sold'] = coin_data.auction.is_sold
                    data['bids'] = coin_data.auction.bids
                
                # If we got good data from JSON-LD, return it
                if data.get('title') and len(data['title']) > 20:
                    return data
                    
            except Exception as e:
                logger.warning(f"Error parsing CNG with JSON-LD parser: {e}")
            
            # Fallback to URL slug parsing if JSON-LD failed
            data = CNGPageParser.parse(html, page.url)
            
            # Try to extract high-res images via JS
            try:
                img_urls = await page.evaluate('''() => {
                    const images = [];
                    document.querySelectorAll('img').forEach(img => {
                        let src = img.src || img.getAttribute('data-src') || img.getAttribute('data-zoom-image');
                        if (src && src.includes('auctionmobility')) {
                            src = src.replace(/width=\\d+/, 'width=1000')
                                     .replace(/height=\\d+/, 'height=1000');
                            if (!images.includes(src)) {
                                images.push(src);
                            }
                        }
                    });
                    return images;
                }''')
                
                if img_urls:
                    coin_images = [u for u in img_urls if '.jpg' in u.lower() or '.png' in u.lower()]
                    if coin_images:
                        data['photos'] = coin_images[:5]
                        data['primary_photo_url'] = coin_images[0]
            except Exception as e:
                logger.warning(f"Error extracting CNG images via JS: {e}")
            
            return data
    
    finally:
        await scraper.stop()


async def scrape_biddr(url: str, config: Optional[BrowserConfig] = None) -> dict:
    """Scrape a Biddr auction lot page with comprehensive metadata extraction.
    
    Uses the rich Biddr parser package for structured data extraction
    including ruler, references, provenance, and more.
    """
    from app.services.scrapers.biddr.parser import BiddrParser
    from app.services.scrapers.biddr.scraper import biddr_data_to_dict
    
    scraper = BrowserScraper(config)
    biddr_parser = BiddrParser()
    
    try:
        await scraper.start()
        
        async with scraper.new_page() as page:
            await scraper._random_delay()
            
            logger.info(f"Fetching Biddr: {url}")
            await page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for content to load
            await asyncio.sleep(3)
            
            try:
                await page.wait_for_selector(
                    'h1, h2, .lot-info, [class*="lot"], [class*="description"]',
                    timeout=10000
                )
            except Exception as e:
                logger.warning(f"Timeout waiting for Biddr page: {e}")
            
            html = await page.content()
            
            # Use the rich Biddr parser
            try:
                coin_data = biddr_parser.parse(html, url)
                
                # Convert to dict format for API
                data = biddr_data_to_dict(coin_data)
                return data
                
            except Exception as e:
                logger.warning(f"Error with Biddr parser: {e}, falling back to basic extraction")
                
                # Fallback: basic extraction from page text
                body_text = await page.evaluate('() => document.body.innerText')
                
                data = {
                    'auction_house': 'Biddr',
                    'url': url,
                    'scraped_at': datetime.utcnow().isoformat(),
                }
                
                # Extract lot number
                lot_match = re.search(r'Lot\s+(\d+)', body_text)
                if lot_match:
                    data['lot_number'] = int(lot_match.group(1))
                
                # Extract description
                desc_match = re.search(r'Description\n([\s\S]*?)(?:Question|Bidding)', body_text, re.I)
                if desc_match:
                    data['description'] = desc_match.group(1).strip()
                    lines = data['description'].split('\n')
                    if lines:
                        data['title'] = lines[0].strip()
                
                # Extract price
                price_match = re.search(r'Price realized\s*([\d,.]+)\s*(EUR|USD|CHF|GBP)', body_text, re.I)
                if price_match:
                    data['hammer_price'] = float(price_match.group(1).replace(',', '.'))
                    data['currency'] = price_match.group(2)
                
                # Extract images
                images = []
                for img in await page.query_selector_all('img[src*="auction_lots"], img[src*="media.biddr"]'):
                    src = await img.get_attribute('src')
                    if src and 'placeholder' not in src:
                        src = src.replace('.s.', '.l.').replace('.m.', '.l.')
                        if src not in images:
                            images.append(src)
                data['photos'] = images
                
                return data
    
    finally:
        await scraper.stop()


async def scrape_ebay(url: str, config: Optional[BrowserConfig] = None) -> dict:
    """Scrape an eBay listing page with comprehensive metadata extraction.
    
    Uses the rich eBay parser package for structured data extraction.
    
    IMPORTANT: eBay data is user-generated and less reliable than auction house data.
    Trust primarily: prices, dates, images, seller info.
    """
    from app.services.scrapers.ebay_rich.parser import EbayParser
    from app.services.scrapers.ebay_rich.scraper import ebay_data_to_dict
    
    scraper = BrowserScraper(config)
    ebay_parser = EbayParser()
    
    try:
        await scraper.start()
        
        async with scraper.new_page() as page:
            await scraper._random_delay()
            
            logger.info(f"Fetching eBay: {url}")
            
            # Use domcontentloaded - networkidle never completes on eBay due to tracking
            await page.goto(url, wait_until='domcontentloaded', timeout=30000)
            
            # Wait for JavaScript to render content
            await asyncio.sleep(5)
            
            selectors_to_try = [
                'h1.x-item-title__mainTitle',
                '.x-item-title',
                '#itemTitle',
                'h1[itemprop="name"]',
                '.vi-title',
            ]
            
            title_found = False
            for sel in selectors_to_try:
                try:
                    await page.wait_for_selector(sel, timeout=5000)
                    title_found = True
                    break
                except:
                    continue
            
            if not title_found:
                logger.warning("No title selector found - page may be expired or blocked")
            
            # Scroll to load lazy content
            await page.evaluate('window.scrollTo(0, document.body.scrollHeight / 2)')
            await asyncio.sleep(1)
            await page.evaluate('window.scrollTo(0, 0)')
            await asyncio.sleep(0.5)
            
            html = await page.content()
            
            # Check if page is expired/removed
            page_text = await page.evaluate('document.body.innerText')
            if 'This listing has ended' in page_text or 'no longer available' in page_text.lower():
                logger.info("eBay listing has ended or is unavailable")
            
            # Use the rich eBay parser
            try:
                coin_data = ebay_parser.parse(html, url)
                
                # Convert to dict format for API
                data = ebay_data_to_dict(coin_data)
                
                # Add fallback extraction via JS if parser returned empty
                if not data.get('title'):
                    js_data = await page.evaluate('''() => {
                        const result = {};
                        
                        // Title - multiple strategies
                        const titleEl = document.querySelector('h1.x-item-title__mainTitle span, h1[itemprop="name"], #itemTitle');
                        if (titleEl) result.title = titleEl.innerText.replace(/^Details about\\s+/i, '').trim();
                        
                        // Price
                        const priceEl = document.querySelector('.x-price-primary span.ux-textspans, [itemprop="price"], #prcIsum');
                        if (priceEl) {
                            const text = priceEl.innerText;
                            const match = text.match(/[\\$€£]?([\\d,]+\\.?\\d*)/);
                            if (match) result.price = parseFloat(match[1].replace(',', ''));
                        }
                        
                        // Sold status
                        if (document.body.innerText.includes('Sold') || 
                            document.querySelector('.vi-VR-cvipPrice, .x-price-approx__price--soldPrice')) {
                            result.is_sold = true;
                        }
                        
                        // Images
                        result.images = [];
                        document.querySelectorAll('img[src*="ebayimg.com"]').forEach(img => {
                            let src = img.src || img.getAttribute('data-zoom-src');
                            if (src && !src.includes('placeholder') && src.length > 50) {
                                src = src.replace(/s-l\\d+/, 's-l1600');
                                if (!result.images.includes(src)) result.images.push(src);
                            }
                        });
                        
                        // Item specifics
                        result.specifics = {};
                        document.querySelectorAll('.ux-labels-values__labels-content, .itemAttr tr').forEach(row => {
                            const label = row.querySelector('.ux-labels-values__labels, td:first-child');
                            const value = row.querySelector('.ux-labels-values__values, td:last-child');
                            if (label && value) {
                                const key = label.innerText.replace(':', '').trim();
                                const val = value.innerText.trim();
                                if (key && val) result.specifics[key] = val;
                            }
                        });
                        
                        // Seller
                        const sellerEl = document.querySelector('.x-sellercard-atf__info a, .mbg-nw a');
                        if (sellerEl) result.seller = sellerEl.innerText.trim();
                        
                        return result;
                    }''')
                    
                    if js_data:
                        if js_data.get('title'):
                            data['title'] = js_data['title']
                        if js_data.get('price'):
                            data['hammer_price'] = js_data['price']
                        if js_data.get('is_sold'):
                            data['is_sold'] = True
                        if js_data.get('images'):
                            data['photos'] = js_data['images'][:10]
                        if js_data.get('specifics'):
                            data['item_specifics'] = js_data['specifics']
                        if js_data.get('seller'):
                            data['seller_username'] = js_data['seller']
                
                return data
                
            except Exception as e:
                logger.warning(f"Error with eBay parser: {e}, falling back to basic extraction")
                
                # Fallback: basic extraction
                data = {
                    'auction_house': 'eBay',
                    'url': url,
                    'scraped_at': datetime.utcnow().isoformat(),
                    '_trust_note': 'eBay data is user-generated. Trust only: prices, dates, images.',
                }
                
                # Extract title
                title_el = await page.query_selector('h1, .x-item-title, #itemTitle')
                if title_el:
                    data['title'] = await title_el.text_content()
                
                # Extract price
                price_el = await page.query_selector('.x-price-primary span, [itemprop="price"]')
                if price_el:
                    text = await price_el.text_content()
                    price_match = re.search(r'[\$€£]?([\d,]+\.?\d*)', text)
                    if price_match:
                        data['hammer_price'] = float(price_match.group(1).replace(',', ''))
                
                # Extract images
                images = []
                for img in await page.query_selector_all('img[src*="ebayimg.com"]'):
                    src = await img.get_attribute('src')
                    if src and 'placeholder' not in src:
                        src = re.sub(r's-l\d+', 's-l1600', src)
                        if src not in images:
                            images.append(src)
                data['photos'] = images[:10]
                
                return data
    
    finally:
        await scraper.stop()


async def scrape_auction_url(url: str, config: Optional[BrowserConfig] = None) -> dict:
    """
    Automatically detect auction house and scrape the page.
    
    Args:
        url: The auction page URL
        config: Optional browser configuration
        
    Returns:
        Parsed auction data dictionary
    """
    url_lower = url.lower()
    
    if 'ha.com' in url_lower or 'heritage' in url_lower:
        return await scrape_heritage(url, config)
    elif 'cngcoins.com' in url_lower or 'auctions.cngcoins.com' in url_lower:
        return await scrape_cng(url, config)
    elif 'biddr.com' in url_lower or 'biddr.ch' in url_lower:
        return await scrape_biddr(url, config)
    elif 'ebay.com' in url_lower or 'ebay.co.uk' in url_lower or 'ebay.de' in url_lower:
        return await scrape_ebay(url, config)
    else:
        # Generic scrape - just get HTML
        scraper = BrowserScraper(config)
        try:
            await scraper.start()
            html, final_url = await scraper.fetch_page(url)
            return {
                'url': final_url,
                'html': html[:10000],  # First 10k chars for debugging
                'scraped_at': datetime.utcnow().isoformat(),
            }
        finally:
            await scraper.stop()
