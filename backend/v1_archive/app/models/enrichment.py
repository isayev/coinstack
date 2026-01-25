"""EnrichmentRecord model for tracking suggested field updates from auction data."""

from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text,
    ForeignKey, Boolean, Index
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class EnrichmentRecord(Base):
    """
    Records when auction data has values for fields missing in coin record.
    
    Each record represents a suggested enrichment that can be applied
    to fill in missing coin data.
    """
    
    __tablename__ = "enrichment_records"
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Links to coin and auction data
    coin_id = Column(Integer, ForeignKey("coins.id", ondelete="CASCADE"), nullable=False, index=True)
    auction_data_id = Column(Integer, ForeignKey("auction_data.id", ondelete="CASCADE"), nullable=True)
    audit_run_id = Column(Integer, ForeignKey("audit_runs.id", ondelete="SET NULL"), nullable=True)
    
    # Field to enrich
    field_name = Column(String(50), nullable=False, index=True)
    suggested_value = Column(Text, nullable=False)  # JSON serialized
    
    # Trust context
    source_house = Column(String(50), nullable=False, index=True)
    trust_level = Column(String(20), nullable=False)  # "authoritative", "high", "medium", "low", "untrusted"
    confidence = Column(Float)  # 0-1 based on trust and data quality
    auto_applicable = Column(Boolean, default=False)  # Can be auto-applied based on trust
    
    # Resolution
    status = Column(String(20), default="pending", nullable=False, index=True)  # "pending", "applied", "rejected", "ignored"
    applied_at = Column(DateTime, nullable=True)
    applied = Column(Boolean, default=False)
    rejection_reason = Column(Text)
    
    # Relationships
    coin = relationship("Coin", backref="enrichments")
    auction_data = relationship("AuctionData", backref="enrichments")
    audit_run = relationship("AuditRun", back_populates="enrichments")
    
    # Indexes for common queries
    __table_args__ = (
        Index("ix_enrichment_status_trust", "status", "trust_level"),
        Index("ix_enrichment_coin_status", "coin_id", "status"),
    )
    
    def __repr__(self):
        return f"<EnrichmentRecord {self.id}: {self.field_name} ({self.status})>"
