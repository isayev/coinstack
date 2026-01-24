"""PriceHistory model for tracking price trends by reference type."""
from sqlalchemy import (
    Column, Integer, String, Numeric, Date, DateTime,
    ForeignKey, UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class PriceHistory(Base):
    """
    Price history for a reference type - aggregated from auction data.
    
    Tracks market trends for specific coin types to support valuation
    and collection analysis.
    """
    
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Link to reference type
    reference_type_id = Column(
        Integer, 
        ForeignKey("reference_types.id", ondelete="CASCADE"), 
        nullable=False, 
        index=True
    )
    
    # Time period
    period_date = Column(Date, nullable=False, index=True)  # Month/quarter start date
    period_type = Column(String(20), default="monthly")     # "monthly", "quarterly", "yearly"
    
    # Price statistics (USD)
    min_price = Column(Numeric(10, 2))
    max_price = Column(Numeric(10, 2))
    median_price = Column(Numeric(10, 2))
    mean_price = Column(Numeric(10, 2))
    
    # Volume
    comp_count = Column(Integer, default=0)        # Number of sales in period
    sold_count = Column(Integer, default=0)        # Successfully sold
    passed_count = Column(Integer, default=0)      # Unsold/passed
    
    # Grade-adjusted metrics (VF equivalent)
    median_price_vf_adj = Column(Numeric(10, 2))   # Adjusted to VF baseline
    
    # Relationship
    reference_type = relationship("ReferenceType", back_populates="price_history")
    
    # Unique constraint - one record per type per period
    __table_args__ = (
        UniqueConstraint('reference_type_id', 'period_date', 'period_type', name='uq_price_history_period'),
    )
