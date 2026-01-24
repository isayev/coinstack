"""
CNG Scraper Data Models

Pydantic schemas for structured coin data extracted from CNG auction listings.
"""

from pydantic import BaseModel, Field, field_validator, computed_field
from typing import Optional
from datetime import datetime
from enum import Enum
import re


class CNGAuctionType(str, Enum):
    """CNG auction types"""
    TRITON = "triton"
    ELECTRONIC = "electronic"
    FEATURE = "feature"
    MAIL_BID = "mail_bid"


class CNGMetal(str, Enum):
    """Metal types"""
    GOLD = "AV"
    SILVER = "AR"
    BILLON = "BI"
    BRONZE = "Æ"
    COPPER = "AE"
    ELECTRUM = "EL"
    LEAD = "PB"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHYSICAL DATA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class PhysicalData(BaseModel):
    """Physical measurements extracted from title"""
    diameter_mm: Optional[float] = None
    weight_g: Optional[float] = None
    die_axis_hours: Optional[int] = None
    
    @computed_field
    @property
    def die_axis_degrees(self) -> Optional[int]:
        if self.die_axis_hours:
            return (self.die_axis_hours * 30) % 360
        return None
    
    @field_validator('die_axis_hours')
    @classmethod
    def validate_die_axis(cls, v):
        if v is not None and not (1 <= v <= 12):
            return None  # Invalid, set to None
        return v


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# REFERENCES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class CatalogReference(BaseModel):
    """Single catalog reference"""
    catalog: str          # "RIC", "Crawford", "RSC", "Sear", "MIR"
    volume: Optional[str] = None  # "III", "II.1"
    number: str           # "676", "44/5"
    suffix: Optional[str] = None  # "(Aurelius)", "var."
    raw_text: str         # Original: "RIC III 676 (Aurelius)"
    
    @computed_field
    @property
    def normalized(self) -> str:
        """Normalized form for matching"""
        parts = [self.catalog]
        if self.volume:
            parts.append(self.volume)
        parts.append(self.number)
        return " ".join(parts)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PROVENANCE
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class ProvenanceEntry(BaseModel):
    """Single provenance entry in the chain"""
    source_type: str      # "auction", "collection", "dealer", "unknown"
    source_name: str      # "Hirsch 279", "Berlin surgeon Collection"
    date: Optional[str] = None  # "8 February 2012", "before 1895"
    lot_number: Optional[str] = None
    price: Optional[str] = None
    notes: Optional[str] = None
    raw_text: str         # Original text


class Provenance(BaseModel):
    """Complete provenance data"""
    entries: list[ProvenanceEntry] = Field(default_factory=list)
    pedigree_year: Optional[int] = None  # Earliest documented year
    historical_notes: Optional[str] = None  # Extended narrative
    raw_text: str = ""
    
    @computed_field
    @property
    def has_provenance(self) -> bool:
        return len(self.entries) > 0 or self.pedigree_year is not None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# IMAGES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class CNGImage(BaseModel):
    """Image from CNG listing"""
    url: str
    url_full_res: Optional[str] = None  # Without size constraints
    index: int = 0
    image_type: str = "combined"  # "obverse", "reverse", "combined"
    local_path: Optional[str] = None
    
    @field_validator('url')
    @classmethod
    def extract_full_res(cls, v):
        # Remove size constraints from URL for full resolution
        return re.sub(r'\s*\?\s*maxwidth=\d+&maxheight=\d+', '', v)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AUCTION DATA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class AuctionInfo(BaseModel):
    """Auction-specific data"""
    auction_name: str     # "Electronic Auction 562"
    auction_type: CNGAuctionType = CNGAuctionType.ELECTRONIC
    lot_number: int = 0
    estimate_usd: Optional[int] = None
    sold_price_usd: Optional[int] = None
    bids: Optional[int] = None
    closing_date: Optional[datetime] = None
    is_sold: bool = False
    buyers_premium_pct: float = 20.0


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN COIN DATA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class CNGCoinData(BaseModel):
    """
    Complete structured data from a CNG coin listing.
    
    This is the main output of the scraper.
    """
    
    # ─── Identifiers ───
    cng_lot_id: str                   # "4-DJ6RZM" (unique across all auctions)
    url: str
    
    # ─── Basic Info ───
    title: str                        # Full title line
    ruler: Optional[str] = None       # "Faustina Junior"
    ruler_title: Optional[str] = None # "Augusta"
    reign_dates: Optional[str] = None # "AD 147-175"
    
    # ─── Coin Type ───
    denomination: Optional[str] = None      # "Denarius"
    metal: Optional[CNGMetal] = None        # AR, AV, Æ
    mint: Optional[str] = None              # "Rome"
    struck_dates: Optional[str] = None      # "circa AD 161"
    struck_under: Optional[str] = None      # "Marcus Aurelius and Lucius Verus"
    
    # ─── Physical ───
    physical: PhysicalData = Field(default_factory=PhysicalData)
    
    # ─── Descriptions ───
    obverse_description: Optional[str] = None
    reverse_description: Optional[str] = None
    
    # ─── References ───
    references: list[CatalogReference] = Field(default_factory=list)
    
    # ─── Condition ───
    grade: Optional[str] = None       # "VF"
    condition_notes: Optional[str] = None  # "Deep, old cabinet toning..."
    
    # ─── Provenance ───
    provenance: Provenance = Field(default_factory=Provenance)
    
    # ─── Categories ───
    categories: list[str] = Field(default_factory=list)  # ["Roman Imperial", "Silver"]
    
    # ─── Auction ───
    auction: Optional[AuctionInfo] = None
    
    # ─── Images ───
    images: list[CNGImage] = Field(default_factory=list)
    
    # ─── Metadata ───
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
    raw_description: str = ""
    
    @computed_field
    @property
    def primary_reference(self) -> Optional[str]:
        """First/primary catalog reference"""
        if self.references:
            return self.references[0].normalized
        return None
    
    @computed_field
    @property
    def has_provenance(self) -> bool:
        return self.provenance.has_provenance
    
    @computed_field
    @property
    def total_price_usd(self) -> Optional[int]:
        """Total price including buyer's premium"""
        if self.auction and self.auction.sold_price_usd:
            premium = 1 + (self.auction.buyers_premium_pct / 100)
            return int(self.auction.sold_price_usd * premium)
        return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# SEARCH RESULTS
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class CNGSearchResult(BaseModel):
    """Single result from search listing"""
    lot_id: str
    lot_number: int
    title: str
    url: str
    thumbnail_url: Optional[str] = None
    estimate_usd: Optional[int] = None
    sold_price_usd: Optional[int] = None
    is_sold: bool = False
    pedigree_year: Optional[int] = None  # From "Pedigreed to XXXX" badge


class CNGSearchResults(BaseModel):
    """Search results page"""
    query: str
    total_results: int
    page: int
    per_page: int
    results: list[CNGSearchResult]
    has_more: bool
