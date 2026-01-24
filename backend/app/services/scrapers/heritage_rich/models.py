"""
Heritage Auctions Scraper Data Models

Pydantic schemas for structured coin data extracted from Heritage Auctions listings.
Heritage is the world's largest numismatic auction house with extensive NGC/PCGS data.
"""

from pydantic import BaseModel, Field, field_validator, computed_field
from typing import Optional, Any
from datetime import datetime, date
from enum import Enum
import re


class HeritageAuctionType(str, Enum):
    """Heritage auction types"""
    SIGNATURE = "signature"       # Major themed auctions
    SHOWCASE = "showcase"         # Showcase auctions
    WEEKLY = "weekly"            # Weekly internet auctions
    MONTHLY = "monthly"          # Monthly internet auctions
    SPECIAL = "special"          # Special events
    BUY_NOW = "buy_now"          # Fixed price


class HeritageMetal(str, Enum):
    """Metal types"""
    GOLD = "AV"
    SILVER = "AR"
    BILLON = "BI"
    BRONZE = "AE"
    COPPER = "AE"
    ELECTRUM = "EL"
    LEAD = "PB"
    ORICHALCUM = "Orichalcum"


class GradingService(str, Enum):
    """Third-party grading services"""
    NGC = "NGC"
    PCGS = "PCGS"
    ANACS = "ANACS"
    ICG = "ICG"
    RAW = "Raw"


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# GRADING
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class SlabGrade(BaseModel):
    """NGC/PCGS slab grade for ancient coins"""
    service: GradingService
    grade: str                    # "MS", "AU", "XF", "VF", "Fine", "VG", "Good"
    strike_score: Optional[str] = None   # "4/5", "5/5" - NGC ancients
    surface_score: Optional[str] = None  # "4/5", "3/5" - NGC ancients
    numeric_grade: Optional[int] = None  # 1-70 scale
    designation: Optional[str] = None    # "Choice", "Fine Style", "Silvering"
    certification_number: Optional[str] = None
    verification_url: Optional[str] = None
    
    @computed_field
    @property
    def full_grade(self) -> str:
        """Full grade string like 'NGC MS 4/5 - 4/5, Fine Style'"""
        parts = [self.service.value]
        
        if self.designation and 'Choice' in self.designation:
            parts.append('Choice')
        
        parts.append(self.grade)
        
        if self.numeric_grade:
            parts[-1] = f"{self.grade} {self.numeric_grade}"
        
        if self.strike_score and self.surface_score:
            parts.append(f"{self.strike_score} - {self.surface_score}")
        
        if self.designation:
            extra = [d for d in self.designation.split(',') if 'Choice' not in d]
            if extra:
                parts.extend([d.strip() for d in extra])
        
        return ' '.join(parts)


class RawGrade(BaseModel):
    """Non-slabbed (raw) coin grade"""
    grade: str                    # "Choice VF", "XF", "VF", etc.
    qualifier: Optional[str] = None  # "altered surface", "tooled", "scratches"
    
    @computed_field
    @property
    def full_grade(self) -> str:
        if self.qualifier:
            return f"{self.grade}, {self.qualifier}"
        return self.grade


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# PHYSICAL DATA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class PhysicalData(BaseModel):
    """Physical measurements from Heritage listing"""
    diameter_mm: Optional[float] = None
    weight_gm: Optional[float] = None   # Heritage uses "gm" not "g"
    die_axis_hours: Optional[int] = None
    
    @computed_field
    @property
    def die_axis_degrees(self) -> Optional[int]:
        if self.die_axis_hours:
            return (self.die_axis_hours * 30) % 360
        return None
    
    @computed_field
    @property
    def weight_g(self) -> Optional[float]:
        """Alias for compatibility"""
        return self.weight_gm


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# REFERENCES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class CatalogReference(BaseModel):
    """Single catalog reference"""
    catalog: str          # "RIC", "Crawford", "RSC", "Sear"
    volume: Optional[str] = None  # "II.1", "V.I"
    number: str           # "756", "44/5"
    suffix: Optional[str] = None
    raw_text: str
    
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
    """Single provenance entry"""
    source_type: str      # "collection", "dealer", "auction", "private_sale"
    source_name: str
    date: Optional[str] = None
    lot_number: Optional[str] = None
    notes: Optional[str] = None
    raw_text: str


class Provenance(BaseModel):
    """Complete provenance data"""
    entries: list[ProvenanceEntry] = Field(default_factory=list)
    collection_name: Optional[str] = None  # Named collection (e.g., "Merrill A. Gibson Collection")
    raw_text: str = ""
    
    @computed_field
    @property
    def has_provenance(self) -> bool:
        return len(self.entries) > 0 or self.collection_name is not None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# IMAGES
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class HeritageImage(BaseModel):
    """Image from Heritage listing"""
    url: str
    url_thumbnail: Optional[str] = None
    url_full_res: Optional[str] = None
    index: int = 0
    image_type: str = "coin"  # "coin", "slab_front", "slab_back", "detail"
    source: str = "heritage"  # "heritage", "ngc_photovision"
    local_path: Optional[str] = None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# AUCTION DATA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class AuctionInfo(BaseModel):
    """Auction-specific data"""
    auction_id: int           # e.g., 61519
    auction_name: str = ""    # "2025 September 21 The Merrill A. Gibson Collection..."
    auction_type: Optional[HeritageAuctionType] = None
    lot_number: int = 0
    auction_date: Optional[date] = None
    sold_price_usd: Optional[int] = None
    estimate_low_usd: Optional[int] = None
    estimate_high_usd: Optional[int] = None
    is_sold: bool = False
    page_views: Optional[int] = None
    buyers_premium_pct: float = 20.0
    bids: Optional[int] = None
    
    @computed_field
    @property
    def total_price_usd(self) -> Optional[int]:
        """Total including buyer's premium"""
        if self.sold_price_usd:
            return int(self.sold_price_usd * (1 + self.buyers_premium_pct / 100))
        return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# MAIN COIN DATA
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class HeritageCoinData(BaseModel):
    """
    Complete structured data from a Heritage Auctions coin listing.
    
    Heritage-specific features:
    - NGC/PCGS slab grades with certification numbers
    - Named collection provenance (e.g., "Merrill A. Gibson Collection")
    - Historical narratives about rulers
    - NGC PhotoVision image links
    """
    
    # ─── Identifiers ───
    heritage_lot_id: str          # "{auction_id}-{lot_number}" e.g., "61519-25316"
    url: str
    
    # ─── Category ───
    category: str = ""            # "Roman Imperial", "Roman Provincial", "Greek"
    subcategory: Optional[str] = None
    
    # ─── Basic Info ───
    title: str = ""               # Full title line
    ruler: Optional[str] = None   # "Gallienus"
    ruler_title: Optional[str] = None  # "Sole Reign", "as Augustus"
    reign_dates: Optional[str] = None  # "AD 253-268"
    
    # ─── Coin Type ───
    denomination: Optional[str] = None  # "antoninianus", "denarius", "as"
    metal: Optional[HeritageMetal] = None
    mint: Optional[str] = None
    mint_date: Optional[str] = None  # "AD 92-94"
    
    # ─── Physical ───
    physical: PhysicalData = Field(default_factory=PhysicalData)
    
    # ─── Grading ───
    is_slabbed: bool = False
    slab_grade: Optional[SlabGrade] = None
    raw_grade: Optional[RawGrade] = None
    
    # ─── Legends & Descriptions ───
    obverse_legend: Optional[str] = None   # "IMP CAES DOMIT AVG GERM-COS XVI CENS PER P P"
    obverse_description: Optional[str] = None  # "laureate head of Domitian right"
    reverse_legend: Optional[str] = None   # "MONETA-AVGVSTI"
    reverse_description: Optional[str] = None
    exergue: Optional[str] = None
    
    # ─── References ───
    references: list[CatalogReference] = Field(default_factory=list)
    
    # ─── Condition Notes ───
    condition_notes: Optional[str] = None  # "Deep kaitoke green patina"
    surface_issues: Optional[str] = None   # "altered surface", "tooled"
    
    # ─── Provenance ───
    provenance: Provenance = Field(default_factory=Provenance)
    
    # ─── Historical Notes ───
    historical_notes: Optional[str] = None  # Extended narrative about ruler/coin
    
    # ─── Auction ───
    auction: Optional[AuctionInfo] = None
    
    # ─── Images ───
    images: list[HeritageImage] = Field(default_factory=list)
    
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
    def grade_display(self) -> Optional[str]:
        """Display grade string"""
        if self.is_slabbed and self.slab_grade:
            return self.slab_grade.full_grade
        elif self.raw_grade:
            return self.raw_grade.full_grade
        return None
    
    @computed_field
    @property
    def certification_number(self) -> Optional[str]:
        """NGC/PCGS certification number if slabbed"""
        if self.slab_grade:
            return self.slab_grade.certification_number
        return None
    
    @computed_field
    @property
    def auction_house(self) -> str:
        return "Heritage Auctions"
