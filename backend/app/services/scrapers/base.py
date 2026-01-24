"""Base auction scraper interface and data models."""

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, HttpUrl
import httpx
import logging

logger = logging.getLogger(__name__)


class LotData(BaseModel):
    """Standardized lot data extracted from auction pages."""
    
    # ─────────────────────────────────────────────────────────────────────────
    # IDENTIFICATION
    # ─────────────────────────────────────────────────────────────────────────
    lot_id: str
    house: str  # "Heritage", "CNG", "Biddr", "eBay", "Agora"
    sub_house: str | None = None  # For Biddr: "Savoca", "Nummitra", etc.
    url: str
    
    # ─────────────────────────────────────────────────────────────────────────
    # PRICING
    # ─────────────────────────────────────────────────────────────────────────
    hammer_price: float | None = None
    estimate_low: float | None = None
    estimate_high: float | None = None
    total_price: float | None = None  # Including buyer's premium
    currency: str = "USD"
    sold: bool = True
    bids: int | None = None
    buyers_premium_pct: float | None = None
    
    # ─────────────────────────────────────────────────────────────────────────
    # AUCTION INFO
    # ─────────────────────────────────────────────────────────────────────────
    sale_name: str | None = None
    lot_number: str | None = None
    auction_date: date | None = None
    closing_date: datetime | None = None
    
    # ─────────────────────────────────────────────────────────────────────────
    # RULER & CLASSIFICATION
    # ─────────────────────────────────────────────────────────────────────────
    ruler: str | None = None
    ruler_title: str | None = None
    reign_dates: str | None = None
    era: str | None = None  # "Roman Republic", "Roman Imperial", "Greek"
    
    # ─────────────────────────────────────────────────────────────────────────
    # COIN TYPE
    # ─────────────────────────────────────────────────────────────────────────
    denomination: str | None = None
    metal: str | None = None  # "AR", "AV", "AE"
    mint: str | None = None
    struck_dates: str | None = None
    struck_under: str | None = None
    
    # ─────────────────────────────────────────────────────────────────────────
    # PHYSICAL MEASUREMENTS
    # ─────────────────────────────────────────────────────────────────────────
    weight_g: float | None = None
    diameter_mm: float | None = None
    thickness_mm: float | None = None
    die_axis: int | None = None  # In hours (1-12)
    
    # ─────────────────────────────────────────────────────────────────────────
    # DESCRIPTIONS
    # ─────────────────────────────────────────────────────────────────────────
    title: str | None = None
    description: str | None = None  # Full raw description
    obverse_description: str | None = None
    reverse_description: str | None = None
    exergue: str | None = None
    
    # ─────────────────────────────────────────────────────────────────────────
    # CONDITION & GRADING
    # ─────────────────────────────────────────────────────────────────────────
    grade: str | None = None
    grade_service: str | None = None  # "NGC", "PCGS"
    certification_number: str | None = None
    condition_notes: str | None = None
    
    # ─────────────────────────────────────────────────────────────────────────
    # CATALOG REFERENCES
    # ─────────────────────────────────────────────────────────────────────────
    catalog_references: list[str] = []  # Normalized: ["RIC III 676"]
    catalog_references_raw: list[str] = []  # Raw: ["RIC III 676 (Aurelius)"]
    primary_reference: str | None = None
    
    # ─────────────────────────────────────────────────────────────────────────
    # PROVENANCE
    # ─────────────────────────────────────────────────────────────────────────
    provenance_text: str | None = None
    pedigree_year: int | None = None
    has_provenance: bool = False
    provenance_entries: list[dict] | None = None
    
    # ─────────────────────────────────────────────────────────────────────────
    # PHOTOS
    # ─────────────────────────────────────────────────────────────────────────
    photos: list[str] = []
    primary_photo_url: str | None = None
    
    # ─────────────────────────────────────────────────────────────────────────
    # EBAY-SPECIFIC
    # ─────────────────────────────────────────────────────────────────────────
    seller_username: str | None = None
    seller_feedback_score: int | None = None
    seller_feedback_pct: float | None = None
    seller_is_top_rated: bool | None = None
    seller_location: str | None = None
    listing_type: str | None = None  # "auction", "buy_it_now", "best_offer"
    shipping_cost: float | None = None
    watchers: int | None = None
    
    # ─────────────────────────────────────────────────────────────────────────
    # METADATA
    # ─────────────────────────────────────────────────────────────────────────
    categories: list[str] = []
    raw_data: dict | None = None  # Store full raw response for debugging
    fetched_at: datetime | None = None


class ScrapeResult(BaseModel):
    """Result from a scrape operation."""
    
    status: Literal["success", "partial", "not_found", "error", "rate_limited"]
    lot_data: LotData | None = None
    error_message: str | None = None
    http_status: int | None = None
    
    # For tracking
    url: str
    house: str | None = None
    elapsed_ms: int | None = None


class AuctionScraperBase(ABC):
    """
    Abstract base class for auction scrapers.
    
    Each auction platform (Heritage, CNG, eBay, etc.) implements this interface.
    """
    
    # Configuration - override in subclasses
    HOUSE: str = ""
    BASE_URL: str = ""
    TIMEOUT: float = 30.0
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    # URL patterns for detection
    URL_PATTERNS: list[str] = []
    
    def __init__(self, timeout: float | None = None, user_agent: str | None = None):
        """Initialize scraper with optional custom settings."""
        self.timeout = timeout or self.TIMEOUT
        self.user_agent = user_agent or self.USER_AGENT
    
    def detect_url(self, url: str) -> bool:
        """
        Check if this scraper can handle the given URL.
        
        Args:
            url: The auction URL to check
            
        Returns:
            True if this scraper can handle the URL
        """
        url_lower = url.lower()
        return any(pattern in url_lower for pattern in self.URL_PATTERNS)
    
    @abstractmethod
    async def extract_lot(self, url: str) -> ScrapeResult:
        """
        Extract lot data from an auction page.
        
        Args:
            url: The auction lot URL
            
        Returns:
            ScrapeResult with extracted data or error info
        """
        pass
    
    @abstractmethod
    def parse_lot_id(self, url: str) -> str | None:
        """
        Extract lot ID from URL.
        
        Args:
            url: The auction URL
            
        Returns:
            Lot ID string or None if not parseable
        """
        pass
    
    async def _fetch_page(self, url: str) -> tuple[str | None, int]:
        """
        Fetch page HTML with standard headers.
        
        Args:
            url: URL to fetch
            
        Returns:
            Tuple of (html_content, status_code)
        """
        headers = {
            "User-Agent": self.user_agent,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "Connection": "keep-alive",
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers, follow_redirects=True)
                return response.text, response.status_code
        except httpx.TimeoutException:
            logger.warning(f"Timeout fetching {url}")
            return None, 408
        except httpx.HTTPError as e:
            logger.warning(f"HTTP error fetching {url}: {e}")
            return None, 500
    
    def _parse_price(self, text: str | None) -> float | None:
        """Parse price string to float, handling various formats."""
        if not text:
            return None
        
        # Remove currency symbols and formatting
        import re
        cleaned = re.sub(r'[^\d.,]', '', text.strip())
        
        # Handle European format (1.234,56) vs US format (1,234.56)
        if ',' in cleaned and '.' in cleaned:
            if cleaned.rfind(',') > cleaned.rfind('.'):
                # European format
                cleaned = cleaned.replace('.', '').replace(',', '.')
            else:
                # US format
                cleaned = cleaned.replace(',', '')
        elif ',' in cleaned:
            # Could be either - check position
            parts = cleaned.split(',')
            if len(parts) == 2 and len(parts[1]) == 2:
                # Likely decimal separator
                cleaned = cleaned.replace(',', '.')
            else:
                # Likely thousands separator
                cleaned = cleaned.replace(',', '')
        
        try:
            return float(cleaned) if cleaned else None
        except ValueError:
            return None
    
    def _parse_date(self, text: str | None) -> date | None:
        """Parse date string to date object."""
        if not text:
            return None
        
        from dateutil import parser
        try:
            return parser.parse(text, fuzzy=True).date()
        except (ValueError, TypeError):
            return None
    
    def _clean_text(self, text: str | None) -> str | None:
        """Clean and normalize text content."""
        if not text:
            return None
        
        import re
        # Normalize whitespace
        cleaned = re.sub(r'\s+', ' ', text.strip())
        return cleaned if cleaned else None
