from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional, List
from decimal import Decimal

@dataclass(frozen=True)
class AuctionLot:
    """Domain entity representing a lot from an auction house."""
    source: str # Heritage, CNG, etc.
    lot_id: str
    url: str
    
    # Auction Info
    sale_name: Optional[str] = None
    lot_number: Optional[str] = None
    auction_date: Optional[date] = None
    
    # Pricing
    estimate_low: Optional[Decimal] = None
    estimate_high: Optional[Decimal] = None
    hammer_price: Optional[Decimal] = None
    currency: str = "USD"
    
    # Attribution
    issuer: Optional[str] = None
    mint: Optional[str] = None
    year_start: Optional[int] = None
    year_end: Optional[int] = None
    
    # Physics
    weight_g: Optional[Decimal] = None
    diameter_mm: Optional[Decimal] = None
    die_axis: Optional[int] = None
    
    # Grading
    grade: Optional[str] = None
    service: Optional[str] = None
    
    # Description
    description: Optional[str] = None
    
    # Images
    primary_image_url: Optional[str] = None
    additional_images: List[str] = field(default_factory=list)
