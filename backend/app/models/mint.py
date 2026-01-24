"""Mint model."""
from sqlalchemy import Column, Integer, String, Numeric
from sqlalchemy.orm import relationship
from app.database import Base


class Mint(Base):
    """Mint location model."""
    
    __tablename__ = "mints"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    province = Column(String(100))
    modern_location = Column(String(100))
    latitude = Column(Numeric(9, 6))
    longitude = Column(Numeric(9, 6))
    
    coins = relationship("Coin", back_populates="mint")
