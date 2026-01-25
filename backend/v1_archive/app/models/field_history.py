"""FieldHistory model for tracking field changes and enabling rollback."""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class FieldHistory(Base):
    """
    Track all field changes for audit trail and rollback capability.
    
    Every auto-merge, manual edit, or rollback operation creates a record here.
    The batch_id groups related changes for batch rollback operations.
    """
    __tablename__ = "field_history"
    
    id = Column(Integer, primary_key=True)
    coin_id = Column(Integer, ForeignKey("coins.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # What changed
    field_name = Column(String(50), nullable=False)
    old_value = Column(JSON)  # Store as JSON for any type (string, number, null)
    new_value = Column(JSON)
    
    # Source tracking
    old_source = Column(String(50))  # "cng", "heritage", "user", null
    new_source = Column(String(50))
    old_source_id = Column(String(100))  # Lot ID or reference
    new_source_id = Column(String(100))
    
    # Change metadata
    change_type = Column(String(20), nullable=False)  # "auto_fill", "auto_update", "manual", "rollback"
    changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    changed_by = Column(String(100))  # "system:auto_merge", "system:campaign", "user"
    
    # Batch tracking for grouped rollback
    batch_id = Column(String(36), index=True)  # UUID for grouping batch operations
    
    # Additional context
    conflict_type = Column(String(50))  # "measurement_tolerance", "grade_minor", etc.
    trust_old = Column(Integer)  # Trust level of old source
    trust_new = Column(Integer)  # Trust level of new source
    reason = Column(String(500))  # Human-readable reason for the change
    
    # Relationships
    coin = relationship("Coin", back_populates="field_history")
    
    # Indexes for common queries
    __table_args__ = (
        Index('ix_field_history_batch_coin', 'batch_id', 'coin_id'),
        Index('ix_field_history_coin_field', 'coin_id', 'field_name'),
    )
    
    def __repr__(self):
        return f"<FieldHistory {self.coin_id}.{self.field_name}: {self.old_value} -> {self.new_value}>"
