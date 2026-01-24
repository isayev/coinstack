"""Coin image model."""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum, DateTime
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


class CoinImage(Base):
    """Coin image model."""
    
    __tablename__ = "coin_images"
    
    id = Column(Integer, primary_key=True)
    coin_id = Column(Integer, ForeignKey("coins.id", ondelete="CASCADE"), nullable=False, index=True)
    
    image_type = Column(Enum(ImageType), nullable=False)
    file_path = Column(String(255), nullable=False)
    file_name = Column(String(100))
    mime_type = Column(String(50))
    size_bytes = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)
    is_primary = Column(Boolean, default=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    coin = relationship("Coin", back_populates="images")
