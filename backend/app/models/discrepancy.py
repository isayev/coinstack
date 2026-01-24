"""DiscrepancyRecord model for tracking data conflicts between coins and auction data."""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text,
    ForeignKey, Boolean, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class DiscrepancyRecord(Base):
    """
    Records when coin data conflicts with auction data.
    
    Each record represents a single field discrepancy that needs
    manual review before resolution.
    """
    
    __tablename__ = "discrepancy_records"
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Links to coin and auction data
    coin_id = Column(Integer, ForeignKey("coins.id", ondelete="CASCADE"), nullable=False, index=True)
    auction_data_id = Column(Integer, ForeignKey("auction_data.id", ondelete="CASCADE"), nullable=True)
    audit_run_id = Column(Integer, ForeignKey("audit_runs.id", ondelete="SET NULL"), nullable=True)
    
    # Field being compared
    field_name = Column(String(50), nullable=False, index=True)
    
    # Values (JSON serialized for complex types)
    current_value = Column(Text)  # Value in coin record
    auction_value = Column(Text)  # Value from auction
    
    # Comparison result
    similarity = Column(Float)  # 0-1 similarity score
    difference_type = Column(String(30))  # "exact", "equivalent", "within_tolerance", "mismatch", "format_diff", "adjacent"
    comparison_notes = Column(Text)  # Explanation from comparator
    
    # Normalized values (for display)
    normalized_current = Column(Text)
    normalized_auction = Column(Text)
    
    # Trust context
    source_house = Column(String(50), nullable=False, index=True)
    trust_level = Column(String(20), nullable=False)  # "authoritative", "high", "medium", "low", "untrusted"
    auto_acceptable = Column(Boolean, default=False)  # Can be auto-accepted based on trust
    
    # Resolution
    status = Column(String(20), default="pending", nullable=False, index=True)  # "pending", "accepted", "rejected", "ignored"
    resolved_at = Column(DateTime, nullable=True)
    resolution = Column(String(20), nullable=True)  # Final resolution action
    resolution_notes = Column(Text)
    
    # Relationships
    coin = relationship("Coin", backref="discrepancies")
    auction_data = relationship("AuctionData", backref="discrepancies")
    audit_run = relationship("AuditRun", back_populates="discrepancies")
    
    # Indexes for common queries
    __table_args__ = (
        Index("ix_discrepancy_status_trust", "status", "trust_level"),
        Index("ix_discrepancy_coin_status", "coin_id", "status"),
    )
    
    def __repr__(self):
        return f"<DiscrepancyRecord {self.id}: {self.field_name} ({self.status})>"
