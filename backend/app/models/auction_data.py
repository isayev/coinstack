"""AuctionData model for tracking auction records and price comparisons."""
from sqlalchemy import (
    Column, Integer, String, Numeric, Date, DateTime, 
    ForeignKey, Boolean, Text, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class AuctionData(Base):
    """
    Auction record data - links to CSV auction data for price tracking.
    
    Tracks auction appearances for your coins and comparable specimens
    for market analysis and valuation.
    """
    
    __tablename__ = "auction_data"
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Link to your coin (nullable for comparables)
    coin_id = Column(Integer, ForeignKey("coins.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Auction identification
    auction_house = Column(String(100), nullable=False, index=True)  # Heritage, CNG, Biddr/Savoca, eBay
    sale_name = Column(String(100))               # "Triton XXIV", "Long Beach 2024"
    lot_number = Column(String(20))
    auction_date = Column(Date, index=True)
    
    # URL - unique constraint ensures no duplicates
    url = Column(String(500), unique=True, nullable=False, index=True)
    
    # Pricing
    estimate_low = Column(Numeric(10, 2))
    estimate_high = Column(Numeric(10, 2))
    hammer_price = Column(Numeric(10, 2))
    total_price = Column(Numeric(10, 2))      # Including buyer's premium
    currency = Column(String(3), default="USD")
    sold = Column(Boolean, default=True)       # False if passed/unsold
    
    # Grading at auction
    grade = Column(String(50))
    grade_service = Column(String(20))
    certification_number = Column(String(50))
    
    # Coin details from listing (for comparables)
    title = Column(String(500))
    description = Column(Text)
    weight_g = Column(Numeric(6, 3))
    diameter_mm = Column(Numeric(5, 2))
    
    # Reference match (for comparables)
    reference_type_id = Column(Integer, ForeignKey("reference_types.id"), nullable=True, index=True)
    
    # Photos from auction
    photos = Column(JSON)                      # List of image URLs
    primary_photo_url = Column(String(500))
    
    # Relationships
    coin = relationship("Coin", back_populates="auction_data")
    reference_type = relationship("ReferenceType")
    provenance_event = relationship("ProvenanceEvent", back_populates="auction_data", uselist=False)
