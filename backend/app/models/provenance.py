"""Provenance event model."""
from sqlalchemy import Column, Integer, String, Date, Numeric, Text, ForeignKey, Enum
from sqlalchemy.orm import relationship
import enum
from app.database import Base


class ProvenanceType(enum.Enum):
    """Provenance event type."""
    AUCTION = "auction"
    PRIVATE_SALE = "private_sale"
    DEALER = "dealer"
    FIND = "find"
    INHERITANCE = "inheritance"
    GIFT = "gift"


class ProvenanceEvent(Base):
    """Provenance event model."""
    
    __tablename__ = "provenance_events"
    
    id = Column(Integer, primary_key=True)
    coin_id = Column(Integer, ForeignKey("coins.id", ondelete="CASCADE"), nullable=False, index=True)
    
    event_type = Column(Enum(ProvenanceType), nullable=False)
    event_date = Column(Date)
    auction_house = Column(String(100))
    sale_name = Column(String(100))
    lot_number = Column(String(20))
    collection_name = Column(String(100))
    price = Column(Numeric(10, 2))
    currency = Column(String(3))
    url = Column(String(500))
    notes = Column(Text)
    sort_order = Column(Integer, default=0)
    
    coin = relationship("Coin", back_populates="provenance_events")
