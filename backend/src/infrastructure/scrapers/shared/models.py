"""
Shared Scraper Data Models

Unified Pydantic models used across all auction house scrapers.
These replace the duplicate models in heritage/models.py, cng/models.py, etc.

Key design decisions:
- Use `weight_g` (not `weight_gm`) for consistency
- Include `needs_verification` flag for user-generated data (eBay)
- Include optional `source` field to track data origin
"""

from pydantic import BaseModel, Field, field_validator, computed_field
from typing import Optional, List
from datetime import datetime
from enum import Enum


# =============================================================================
# ENUMS
# =============================================================================

class Metal(str, Enum):
    """
    Unified metal types across all scrapers.
    
    Uses standard numismatic abbreviations (AV, AR, AE, etc.)
    """
    GOLD = "AV"           # Aurum
    SILVER = "AR"         # Argentum
    BILLON = "BI"         # Silver-copper alloy
    BRONZE = "AE"         # Aes (copper alloy)
    COPPER = "CU"         # Pure copper
    ELECTRUM = "EL"       # Gold-silver alloy
    LEAD = "PB"           # Plumbum
    ORICHALCUM = "OR"     # Brass (copper-zinc)
    POTIN = "PO"          # Base metal alloy (Celtic)
    
    @classmethod
    def from_string(cls, value: str) -> Optional["Metal"]:
        """Parse metal from various string formats."""
        if not value:
            return None
        
        value_upper = value.upper().strip()
        value_lower = value.lower().strip()
        
        # Direct enum match
        for metal in cls:
            if value_upper == metal.value:
                return metal
        
        # Common alternate names
        mapping = {
            "gold": cls.GOLD,
            "av": cls.GOLD,
            "aureus": cls.GOLD,
            "silver": cls.SILVER,
            "ar": cls.SILVER,
            "denarius": cls.SILVER,
            "bronze": cls.BRONZE,
            "ae": cls.BRONZE,
            "æ": cls.BRONZE,
            "copper": cls.COPPER,
            "cu": cls.COPPER,
            "billon": cls.BILLON,
            "bi": cls.BILLON,
            "electrum": cls.ELECTRUM,
            "el": cls.ELECTRUM,
            "lead": cls.LEAD,
            "pb": cls.LEAD,
            "orichalcum": cls.ORICHALCUM,
            "brass": cls.ORICHALCUM,
            "potin": cls.POTIN,
        }
        
        return mapping.get(value_lower)


class GradingService(str, Enum):
    """Third-party grading services."""
    NGC = "NGC"
    PCGS = "PCGS"
    ANACS = "ANACS"
    ICG = "ICG"
    RAW = "Raw"           # Not professionally graded
    UNKNOWN = "Unknown"


# =============================================================================
# PHYSICAL DATA
# =============================================================================

class PhysicalData(BaseModel):
    """
    Physical measurements for a coin.
    
    Standardized across all scrapers. Uses metric units:
    - Weight in grams (g)
    - Diameter in millimeters (mm)
    - Die axis in clock hours (1-12)
    """
    diameter_mm: Optional[float] = None
    weight_g: Optional[float] = None
    die_axis_hours: Optional[int] = None
    thickness_mm: Optional[float] = None
    
    @computed_field
    @property
    def die_axis_degrees(self) -> Optional[int]:
        """Convert die axis from clock hours to degrees."""
        if self.die_axis_hours is not None:
            return (self.die_axis_hours * 30) % 360
        return None
    
    @field_validator('die_axis_hours')
    @classmethod
    def validate_die_axis(cls, v):
        """Validate die axis is in valid range (1-12 or 0)."""
        if v is not None and not (0 <= v <= 12):
            return None  # Invalid, set to None
        return v
    
    @field_validator('weight_g')
    @classmethod
    def validate_weight(cls, v):
        """Validate weight is positive."""
        if v is not None and v < 0:
            return None
        return v
    
    @field_validator('diameter_mm')
    @classmethod
    def validate_diameter(cls, v):
        """Validate diameter is positive and reasonable."""
        if v is not None and (v < 0 or v > 200):  # Max 200mm
            return None
        return v


# =============================================================================
# CATALOG REFERENCES
# =============================================================================

class CatalogReference(BaseModel):
    """
    Single catalog reference (RIC, Crawford, Sear, etc.)
    
    Unified across all scrapers. For eBay/user-generated data,
    set `needs_verification=True`.
    """
    catalog: str           # "RIC", "Crawford", "RSC", "Sear", "MIR"
    volume: Optional[str] = None   # "II.1", "V.I", "III"
    number: str            # "756", "44/5", "207a"
    suffix: Optional[str] = None   # "(Aurelius)", "var."
    raw_text: str          # Original unparsed text
    
    # Verification flag for user-generated data
    needs_verification: bool = False
    
    @computed_field
    @property
    def normalized(self) -> str:
        """Normalized form for matching/comparison."""
        parts = [self.catalog]
        if self.volume:
            parts.append(self.volume)
        parts.append(self.number)
        return " ".join(parts)
    
    @computed_field
    @property
    def full_reference(self) -> str:
        """Full reference including suffix."""
        ref = self.normalized
        if self.suffix:
            ref += f" {self.suffix}"
        return ref


# =============================================================================
# PROVENANCE
# =============================================================================

class ProvenanceEntry(BaseModel):
    """
    Single provenance entry in a coin's ownership history.
    
    Tracks auctions, collections, dealers, and private sales.
    """
    source_type: str       # "auction", "collection", "dealer", "private_sale", "unknown"
    source_name: str       # "Hirsch 279", "Hunt Collection", "CNG"
    date: Optional[str] = None     # "8 February 2012", "before 1895"
    lot_number: Optional[str] = None
    price: Optional[str] = None    # Original price if known
    notes: Optional[str] = None
    raw_text: str          # Original unparsed text
    
    @classmethod
    def from_auction(
        cls,
        auction_name: str,
        date: Optional[str] = None,
        lot_number: Optional[str] = None,
        raw_text: str = ""
    ) -> "ProvenanceEntry":
        """Factory method for auction provenance."""
        return cls(
            source_type="auction",
            source_name=auction_name,
            date=date,
            lot_number=lot_number,
            raw_text=raw_text or auction_name
        )
    
    @classmethod
    def from_collection(
        cls,
        collection_name: str,
        raw_text: str = ""
    ) -> "ProvenanceEntry":
        """Factory method for collection provenance."""
        return cls(
            source_type="collection",
            source_name=collection_name,
            raw_text=raw_text or collection_name
        )


class Provenance(BaseModel):
    """
    Complete provenance data for a coin.
    """
    entries: List[ProvenanceEntry] = Field(default_factory=list)
    collection_name: Optional[str] = None  # Named collection if applicable
    pedigree_year: Optional[int] = None    # Earliest documented year
    historical_notes: Optional[str] = None # Extended narrative
    raw_text: str = ""
    
    @computed_field
    @property
    def has_provenance(self) -> bool:
        """Check if any provenance data exists."""
        return (
            len(self.entries) > 0 or 
            self.collection_name is not None or
            self.pedigree_year is not None
        )
    
    @computed_field
    @property
    def entry_count(self) -> int:
        """Number of provenance entries."""
        return len(self.entries)


# =============================================================================
# IMAGES
# =============================================================================

class Image(BaseModel):
    """
    Image from auction listing.
    
    Unified model for all scrapers.
    """
    url: str               # Primary URL
    url_thumbnail: Optional[str] = None
    url_full_res: Optional[str] = None
    index: int = 0         # Position in listing (0 = primary)
    image_type: str = "coin"  # "coin", "obverse", "reverse", "combined", "slab_front", "slab_back", "detail"
    source: Optional[str] = None  # "heritage", "cng", "ngc_photovision"
    local_path: Optional[str] = None  # If downloaded locally
    is_stock_photo: bool = False  # eBay may use stock photos
    
    @computed_field
    @property
    def best_url(self) -> str:
        """Return highest resolution URL available."""
        return self.url_full_res or self.url
    
    @field_validator('url')
    @classmethod
    def validate_url(cls, v):
        """Basic URL validation."""
        if not v or not v.startswith(('http://', 'https://')):
            raise ValueError("Invalid image URL")
        return v


# =============================================================================
# GRADING
# =============================================================================

class SlabGrade(BaseModel):
    """
    NGC/PCGS slab grade for ancient coins.
    """
    service: GradingService = GradingService.RAW
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
        """Full grade string like 'NGC MS 4/5 - 4/5, Fine Style'."""
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
    """Non-slabbed (raw) coin grade."""
    grade: str                    # "Choice VF", "XF", "VF", etc.
    qualifier: Optional[str] = None  # "altered surface", "tooled", "scratches"
    
    @computed_field
    @property
    def full_grade(self) -> str:
        if self.qualifier:
            return f"{self.grade}, {self.qualifier}"
        return self.grade
