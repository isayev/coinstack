"""ImageAuctionSource model for tracking image provenance across auctions."""

from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class ImageAuctionSource(Base):
    """
    Tracks which auctions an image appeared in.
    
    Allows one image to be linked to multiple auction appearances
    for provenance tracking and deduplication.
    """
    
    __tablename__ = "image_auction_sources"
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Link to image
    image_id = Column(Integer, ForeignKey("coin_images.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Link to auction
    auction_data_id = Column(Integer, ForeignKey("auction_data.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Original URL from this auction
    source_url = Column(String(500), nullable=False)
    
    # Source metadata
    source_house = Column(String(50))
    fetched_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    image = relationship("CoinImage", back_populates="auction_sources")
    auction_data = relationship("AuctionData", backref="image_sources")
    
    def __repr__(self):
        return f"<ImageAuctionSource {self.id}: image={self.image_id}, auction={self.auction_data_id}>"
