"""
Biddr Scraper Data Models

Pydantic schemas for structured coin data extracted from Biddr auction listings.
Biddr hosts multiple auction houses including Savoca, Roma, Leu, Nomos, Künker, etc.
"""

from pydantic import BaseModel, Field, field_validator, computed_field
from typing import Optional
from datetime import datetime
from enum import Enum
import re

class BiddrSubHouse(str, Enum):
    """Auction houses hosted on Biddr"""
    SAVOCA = "Savoca"
    ROMA = "Roma"
    LEU = "Leu"
    NOMOS = "Nomos"
    KUNKER = "Künker"
    NUMMITRA = "Nummitra"
    REXNUMIS = "RexNumis"
    COIN_CABINET = "Coin Cabinet"
    AGORA = "Agora"
    NUMISMATICA_ARS_CLASSICA = "NAC"
    PECUNEM = "Pecunem"
    UNKNOWN = "Unknown"


class BiddrMetal(str, Enum):
    """Metal types"""
    GOLD = "AV"
    SILVER = "AR"
    BILLON = "BI"
    BRONZE = "AE"
    COPPER = "CU"
    ELECTRUM = "EL"
    LEAD = "PB"
    ORICHALCUM = "OR"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHYSICAL DATA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class BiddrPhysicalData(BaseModel):
    """Physical measurements extracted from listing"""
    diameter_mm: Optional[float] = None
    weight_g: Optional[float] = None
    die_axis_hours: Optional[int] = None
    thickness_mm: Optional[float] = None
    
    @computed_field
    @property
    def die_axis_degrees(self) -> Optional[int]:
        if self.die_axis_hours is not None:
            return (self.die_axis_hours * 30) % 360
        return None
    
    @field_validator('die_axis_hours')
    @classmethod
    def validate_die_axis(cls, v):
        if v is not None and not (0 <= v <= 12):
            return None
        return v


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# REFERENCES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class BiddrCatalogReference(BaseModel):
    """Single catalog reference"""
    catalog: str          # "RIC", "Crawford", "RSC", "Sear", "Sydenham"
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

class BiddrProvenanceEntry(BaseModel):
    """Single provenance entry in the chain"""
    source_type: str      # "auction", "collection", "dealer", "unknown"
    source_name: str      # "Hirsch 279", "Old Swiss Collection"
    date: Optional[str] = None
    lot_number: Optional[str] = None
    raw_text: str


class BiddrProvenance(BaseModel):
    """Complete provenance data"""
    entries: list[BiddrProvenanceEntry] = Field(default_factory=list)
    pedigree_year: Optional[int] = None
    raw_text: str = ""
    
    @computed_field
    @property
    def has_provenance(self) -> bool:
        return len(self.entries) > 0 or self.pedigree_year is not None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# IMAGES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class BiddrImage(BaseModel):
    """Image from Biddr listing"""
    url: str
    url_large: Optional[str] = None
    index: int = 0
    image_type: str = "combined"  # "obverse", "reverse", "combined"
    local_path: Optional[str] = None
    
    @field_validator('url')
    @classmethod
    def upgrade_to_large(cls, v):
        # Upgrade to large version if possible
        return v.replace('.s.', '.l.').replace('.m.', '.l.')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AUCTION DATA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class BiddrAuctionInfo(BaseModel):
    """Auction-specific data"""
    auction_name: str = ""
    auction_id: Optional[int] = None
    lot_number: int = 0
    estimate_low: Optional[float] = None
    estimate_high: Optional[float] = None
    starting_price: Optional[float] = None
    hammer_price: Optional[float] = None
    currency: str = "EUR"
    bids: Optional[int] = None
    closing_date: Optional[datetime] = None
    is_sold: bool = False
    is_closed: bool = False
    buyers_premium_pct: float = 18.0  # Typical for European houses


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN COIN DATA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class BiddrCoinData(BaseModel):
    """
    Complete structured data from a Biddr coin listing.
    """
    
    # ─── Identifiers ───
    biddr_lot_id: str                 # "102-92534" (auction-lot)
    url: str
    sub_house: Optional[BiddrSubHouse] = None
    
    # ─── Basic Info ───
    title: str = ""                   # Full title line
    
    # ─── Ruler & Classification ───
    ruler: Optional[str] = None       # "Titus", "Augustus"
    ruler_title: Optional[str] = None # "As Caesar", "Augusta"
    reign_dates: Optional[str] = None # "AD 69-79", "27 BC - AD 14"
    era: Optional[str] = None         # "Roman Republic", "Roman Imperial"
    
    # ─── Coin Type ───
    denomination: Optional[str] = None      # "Denarius", "Denar"
    metal: Optional[BiddrMetal] = None      # AR, AV, AE
    mint: Optional[str] = None              # "Rome", "Alexandria"
    mint_date: Optional[str] = None         # "circa 189-180 BC"
    struck_under: Optional[str] = None
    
    # ─── Physical ───
    physical: BiddrPhysicalData = Field(default_factory=BiddrPhysicalData)
    
    # ─── Descriptions ───
    obverse_description: Optional[str] = None
    reverse_description: Optional[str] = None
    exergue: Optional[str] = None
    
    # ─── References ───
    references: list[BiddrCatalogReference] = Field(default_factory=list)
    
    # ─── Condition ───
    grade: Optional[str] = None       # "Very Fine", "EF"
    grade_german: Optional[str] = None  # "Sehr schön", "Vorzüglich"
    condition_notes: Optional[str] = None
    
    # ─── Provenance ───
    provenance: BiddrProvenance = Field(default_factory=BiddrProvenance)
    
    # ─── Auction ───
    auction: BiddrAuctionInfo = Field(default_factory=BiddrAuctionInfo)
    
    # ─── Images ───
    images: list[BiddrImage] = Field(default_factory=list)
    
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
    def total_price(self) -> Optional[float]:
        """Total price including buyer's premium"""
        if self.auction and self.auction.hammer_price:
            premium = 1 + (self.auction.buyers_premium_pct / 100)
            return round(self.auction.hammer_price * premium, 2)
        return None
    
    @computed_field
    @property
    def auction_house(self) -> str:
        """Full auction house name"""
        if self.sub_house:
            return f"Biddr/{self.sub_house.value}"
        return "Biddr"
