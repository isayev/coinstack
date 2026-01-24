"""Coin image model with auction source tracking and deduplication support."""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class ImageType(enum.Enum):
    """Image type."""
    OBVERSE = "obverse"
    REVERSE = "reverse"
    EDGE = "edge"
    SLAB = "slab"
    DETAIL = "detail"
    COMBINED = "combined"
    OTHER = "other"


class CoinImage(Base):
    """
    Coin image model with perceptual hashing for deduplication
    and auction source tracking.
    """
    
    __tablename__ = "coin_images"
    
    id = Column(Integer, primary_key=True)
    coin_id = Column(Integer, ForeignKey("coins.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Image metadata
    image_type = Column(Enum(ImageType), nullable=False)
    file_path = Column(String(255), nullable=False)
    file_name = Column(String(100))
    mime_type = Column(String(50))
    size_bytes = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)
    is_primary = Column(Boolean, default=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Deduplication - perceptual hash for finding similar images
    perceptual_hash = Column(String(64), nullable=True, index=True)
    
    # Source tracking - where did this image come from?
    source_url = Column(String(500), nullable=True)  # Original URL
    source_auction_id = Column(Integer, ForeignKey("auction_data.id", ondelete="SET NULL"), nullable=True)
    source_house = Column(String(50), nullable=True)  # "Heritage", "CNG", etc.
    downloaded_at = Column(DateTime, nullable=True)
    
    # Relationships
    coin = relationship("Coin", back_populates="images")
    source_auction = relationship("AuctionData", backref="downloaded_images")
    auction_sources = relationship("ImageAuctionSource", back_populates="image", cascade="all, delete-orphan")
    
    # Index for deduplication queries
    __table_args__ = (
        Index("ix_coin_image_hash", "coin_id", "perceptual_hash"),
    )
