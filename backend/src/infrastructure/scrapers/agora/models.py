"""
Agora Scraper Data Models

Pydantic schemas for structured coin data extracted from Agora Auctions.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class AgoraPhysicalData(BaseModel):
    """Physical measurements"""
    diameter_mm: Optional[float] = None
    weight_g: Optional[float] = None
    die_axis: Optional[int] = None

class AgoraCoinData(BaseModel):
    """
    Structured data from Agora Auctions.
    """
    agora_lot_id: str
    url: str
    
    # Basic Info
    title: str
    description: Optional[str] = None
    
    # Auction Info
    lot_number: Optional[str] = None
    auction_date: Optional[datetime] = None
    
    # Pricing
    estimate_low: Optional[float] = None
    estimate_high: Optional[float] = None
    hammer_price: Optional[float] = None
    currency: str = "USD"
    
    # Physical
    physical: AgoraPhysicalData = Field(default_factory=AgoraPhysicalData)
    
    # Grading
    grade: Optional[str] = None
    grade_service: Optional[str] = None
    certification_number: Optional[str] = None
    
    # References
    references: list[str] = Field(default_factory=list)
    
    # Images
    primary_photo_url: Optional[str] = None
    photos: list[str] = Field(default_factory=list)
    
    # Metadata
    scraped_at: datetime = Field(default_factory=datetime.utcnow)
