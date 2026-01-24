"""Countermark model for provincial coins."""
from sqlalchemy import Column, Integer, String, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class CountermarkType(enum.Enum):
    """Type of countermark."""
    HOST_VALIDATION = "host_validation"
    VALUE_REDUCTION = "value_reduction"
    MILITARY = "military"
    CIVIC = "civic"
    IMPERIAL = "imperial"
    OTHER = "other"


class CountermarkCondition(enum.Enum):
    """Countermark legibility."""
    CLEAR = "clear"
    PARTIAL = "partial"
    WORN = "worn"
    UNCERTAIN = "uncertain"


class CountermarkPlacement(enum.Enum):
    """Which side the countermark is on."""
    OBVERSE = "obverse"
    REVERSE = "reverse"


class Countermark(Base):
    """
    Countermark on a coin - official stamps applied after minting.
    
    Essential for provincial bronze coins where countermarks indicate
    revalidation, military use, or value adjustments.
    """
    
    __tablename__ = "countermarks"
    
    id = Column(Integer, primary_key=True)
    coin_id = Column(Integer, ForeignKey("coins.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Type and description
    countermark_type = Column(Enum(CountermarkType), nullable=False)
    description = Column(String(100), nullable=False)  # "TI·C·A", "NCAPR", "Eagle"
    expanded = Column(String(255))                      # Full expansion of abbreviation
    
    # Location on coin
    placement = Column(Enum(CountermarkPlacement), nullable=False)
    position = Column(String(50))                       # "on portrait", "in field left"
    condition = Column(Enum(CountermarkCondition), default=CountermarkCondition.CLEAR)
    
    # Attribution
    authority = Column(String(100))     # Who applied it (emperor, city, legion)
    date_applied = Column(String(50))   # "AD 79-81", "Flavian"
    
    # Documentation
    image_url = Column(String(500))     # Image showing the countermark
    image_side = Column(Enum(CountermarkPlacement))  # Which side the image shows
    notes = Column(String(255))
    
    # Relationship
    coin = relationship("Coin", back_populates="countermarks")
