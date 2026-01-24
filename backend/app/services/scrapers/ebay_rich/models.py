"""
eBay Scraper Data Models

Pydantic schemas for structured coin data extracted from eBay listings.

IMPORTANT: eBay data is user-generated and less reliable than professional 
auction house data. The following fields should be considered trustworthy:
- Prices (sold_price, current_bid)
- Dates (sale_date, listing_date)
- Images (photos)
- Seller information

Other numismatic data (ruler, references, etc.) should be treated with caution
and verified against authoritative sources.
"""

from pydantic import BaseModel, Field, field_validator, computed_field
from typing import Optional
from datetime import datetime
from enum import Enum
import re


class EbayListingType(str, Enum):
    """eBay listing formats"""
    AUCTION = "auction"
    BUY_IT_NOW = "buy_it_now"
    AUCTION_BIN = "auction_with_bin"  # Auction with Buy It Now option
    BEST_OFFER = "best_offer"
    FIXED_PRICE = "fixed_price"


class EbayCondition(str, Enum):
    """eBay item condition categories"""
    NEW = "New"
    LIKE_NEW = "Like New"
    VERY_GOOD = "Very Good"
    GOOD = "Good"
    ACCEPTABLE = "Acceptable"
    USED = "Used"
    CERTIFIED = "Certified"
    UNGRADED = "Ungraded"


class EbayMetal(str, Enum):
    """Metal types"""
    GOLD = "Gold"
    SILVER = "Silver"
    BRONZE = "Bronze"
    COPPER = "Copper"
    BILLON = "Billon"
    ELECTRUM = "Electrum"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHYSICAL DATA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class EbayPhysicalData(BaseModel):
    """Physical measurements from listing"""
    diameter_mm: Optional[float] = None
    weight_g: Optional[float] = None
    thickness_mm: Optional[float] = None
    
    # eBay often uses different units
    diameter_inches: Optional[float] = None
    weight_oz: Optional[float] = None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# REFERENCES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class EbayCatalogReference(BaseModel):
    """Catalog reference (user-provided, verify independently)"""
    catalog: str          # "RIC", "Crawford", "RSC"
    volume: Optional[str] = None
    number: str
    raw_text: str
    
    # Flag for verification
    needs_verification: bool = True
    
    @computed_field
    @property
    def normalized(self) -> str:
        parts = [self.catalog]
        if self.volume:
            parts.append(self.volume)
        parts.append(self.number)
        return " ".join(parts)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# IMAGES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class EbayImage(BaseModel):
    """Image from eBay listing"""
    url: str
    url_large: Optional[str] = None
    index: int = 0
    is_stock_photo: bool = False  # eBay sometimes uses stock photos
    local_path: Optional[str] = None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SELLER INFO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class EbaySellerInfo(BaseModel):
    """Seller information"""
    username: str = ""
    feedback_score: Optional[int] = None
    feedback_percent: Optional[float] = None
    is_top_rated: bool = False
    is_store: bool = False
    store_name: Optional[str] = None
    location: Optional[str] = None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# LISTING DATA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class EbayListingInfo(BaseModel):
    """eBay listing-specific data"""
    item_id: str = ""
    listing_type: Optional[EbayListingType] = None
    
    # Prices (TRUSTWORTHY)
    current_price: Optional[float] = None
    buy_it_now_price: Optional[float] = None
    sold_price: Optional[float] = None
    shipping_cost: Optional[float] = None
    currency: str = "USD"
    
    # Auction details
    bid_count: Optional[int] = None
    watchers: Optional[int] = None
    
    # Dates (TRUSTWORTHY)
    listing_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    sold_date: Optional[datetime] = None
    
    # Status
    is_sold: bool = False
    is_ended: bool = False
    is_best_offer_accepted: bool = False
    
    # Returns/shipping
    returns_accepted: bool = False
    free_shipping: bool = False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GRADING INFO
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class EbayGradingInfo(BaseModel):
    """Third-party grading information"""
    is_slabbed: bool = False
    grading_service: Optional[str] = None  # NGC, PCGS, ANACS
    grade: Optional[str] = None
    cert_number: Optional[str] = None
    
    # Raw coin grade (user-provided)
    raw_grade: Optional[str] = None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN COIN DATA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class EbayCoinData(BaseModel):
    """
    Complete data from an eBay coin listing.
    
    TRUST LEVELS:
    - HIGH: prices, dates, images, seller info
    - LOW: ruler, references, descriptions (user-generated)
    """
    
    # ─── Identifiers ───
    ebay_item_id: str
    url: str
    
    # ─── Basic Info (LOW TRUST) ───
    title: str = ""
    
    # ─── Coin Details (LOW TRUST - verify independently) ───
    ruler: Optional[str] = None
    reign_dates: Optional[str] = None
    era: Optional[str] = None
    denomination: Optional[str] = None
    metal: Optional[str] = None
    mint: Optional[str] = None
    mint_date: Optional[str] = None
    
    # ─── Physical (MEDIUM TRUST) ───
    physical: EbayPhysicalData = Field(default_factory=EbayPhysicalData)
    
    # ─── Description (LOW TRUST) ───
    description: Optional[str] = None
    item_specifics: dict = Field(default_factory=dict)
    
    # ─── References (LOW TRUST - verify) ───
    references: list[EbayCatalogReference] = Field(default_factory=list)
    
    # ─── Grading ───
    grading: EbayGradingInfo = Field(default_factory=EbayGradingInfo)
    condition: Optional[EbayCondition] = None
    
    # ─── Listing (HIGH TRUST) ───
    listing: EbayListingInfo = Field(default_factory=EbayListingInfo)
    
    # ─── Seller (HIGH TRUST) ───
    seller: EbaySellerInfo = Field(default_factory=EbaySellerInfo)
    
    # ─── Images (HIGH TRUST) ───
    images: list[EbayImage] = Field(default_factory=list)
    
    # ─── Metadata ───
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    
    @computed_field
    @property
    def auction_house(self) -> str:
        return "eBay"
    
    @computed_field
    @property
    def primary_reference(self) -> Optional[str]:
        if self.references:
            return self.references[0].normalized
        return None
    
    @computed_field
    @property
    def final_price(self) -> Optional[float]:
        """Final sale price including shipping"""
        price = self.listing.sold_price or self.listing.current_price
        if price and self.listing.shipping_cost:
            return price + self.listing.shipping_cost
        return price
    
    @computed_field
    @property
    def is_trusted_seller(self) -> bool:
        """Seller meets trust criteria"""
        if not self.seller:
            return False
        return (
            (self.seller.feedback_score or 0) >= 100 and
            (self.seller.feedback_percent or 0) >= 98.0
        )
