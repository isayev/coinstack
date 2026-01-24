"""Coin reference model."""
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class ReferenceSystem(enum.Enum):
    """Reference system."""
    RIC = "ric"
    CRAWFORD = "crawford"
    RPC = "rpc"
    RSC = "rsc"
    BMCRE = "bmcre"
    SEAR = "sear"
    SYDENHAM = "sydenham"
    OTHER = "other"


class CoinReference(Base):
    """Coin reference model."""
    
    __tablename__ = "coin_references"
    
    id = Column(Integer, primary_key=True)
    coin_id = Column(Integer, ForeignKey("coins.id", ondelete="CASCADE"), nullable=False, index=True)
    
    system = Column(Enum(ReferenceSystem), nullable=False)
    volume = Column(String(20))
    number = Column(String(50), nullable=False)
    is_primary = Column(Boolean, default=False)
    plate_coin = Column(Boolean, default=False)
    notes = Column(String(255))
    
    coin = relationship("Coin", back_populates="references")
