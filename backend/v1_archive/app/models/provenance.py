"""Provenance event model - Enhanced with detailed auction fields."""
from sqlalchemy import Column, Integer, String, Date, Numeric, Text, ForeignKey, Enum, Boolean
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
    COLLECTION = "collection"  # From named collection
    EXCHANGE = "exchange"


class ProvenanceEvent(Base):
    """Provenance event model - tracks coin history."""
    
    __tablename__ = "provenance_events"
    
    id = Column(Integer, primary_key=True)
    coin_id = Column(Integer, ForeignKey("coins.id", ondelete="CASCADE"), nullable=False, index=True)
    
    event_type = Column(Enum(ProvenanceType), nullable=False)
    event_date = Column(Date)
    
    # Auction details - decomposed for proper citation
    auction_house = Column(String(100))     # "CNG", "Heritage", "Künker"
    sale_series = Column(String(50))        # "Triton", "Electronic Auction"
    sale_number = Column(String(20))        # "XXIV" or "24"
    lot_number = Column(String(20))
    catalog_reference = Column(String(200)) # Full citation "CNG Triton XXIV, lot 456"
    
    # Pricing - distinguish hammer from total
    hammer_price = Column(Numeric(10, 2))        # Price at hammer fall
    buyers_premium_pct = Column(Numeric(4, 2))   # 20.00 = 20%
    total_price = Column(Numeric(10, 2))         # Final price including premium
    currency = Column(String(3))
    
    # Dealer/Collection details
    dealer_name = Column(String(100))
    collection_name = Column(String(100))        # "Hunt Collection", "BCD Collection"
    
    # Documentation
    url = Column(String(500))
    receipt_available = Column(Boolean, default=False)
    notes = Column(Text)
    sort_order = Column(Integer, default=0)
    
    # Relationship
    coin = relationship("Coin", back_populates="provenance_events")
    
    # Link to AuctionData if from tracked auction
    auction_data_id = Column(Integer, ForeignKey("auction_data.id"), nullable=True)
    auction_data = relationship("AuctionData", back_populates="provenance_event")
