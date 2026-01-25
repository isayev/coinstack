"""AuditRun model for tracking audit execution sessions."""

from sqlalchemy import (
    Column, Integer, String, DateTime, Text, JSON
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class AuditRun(Base):
    """
    Tracks each audit execution session.
    
    Allows monitoring progress of long-running audits and
    provides historical record of audit activities.
    """
    
    __tablename__ = "audit_runs"
    
    id = Column(Integer, primary_key=True)
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, nullable=True)
    
    # Scope of audit
    scope = Column(String(20), nullable=False)  # "single", "all", "selected"
    coin_ids = Column(JSON, nullable=True)  # Array of coin IDs if scope=selected or single
    
    # Progress tracking
    total_coins = Column(Integer, default=0)
    coins_audited = Column(Integer, default=0)
    coins_with_issues = Column(Integer, default=0)
    
    # Results summary
    discrepancies_found = Column(Integer, default=0)
    enrichments_found = Column(Integer, default=0)
    images_downloaded = Column(Integer, default=0)
    auto_accepted = Column(Integer, default=0)
    auto_applied = Column(Integer, default=0)
    
    # Status
    status = Column(String(20), default="running", nullable=False)  # "running", "completed", "failed", "cancelled"
    error_message = Column(Text, nullable=True)
    
    # Configuration used
    config_snapshot = Column(JSON, nullable=True)  # Trust matrix settings at time of run
    
    # Relationships
    discrepancies = relationship("DiscrepancyRecord", back_populates="audit_run")
    enrichments = relationship("EnrichmentRecord", back_populates="audit_run")
    
    def __repr__(self):
        return f"<AuditRun {self.id}: {self.scope} ({self.status})>"
    
    @property
    def progress_percent(self) -> float:
        """Calculate progress percentage."""
        if self.total_coins == 0:
            return 0.0
        return (self.coins_audited / self.total_coins) * 100
    
    @property
    def duration_seconds(self) -> float | None:
        """Calculate duration in seconds."""
        if not self.completed_at:
            return (datetime.utcnow() - self.started_at).total_seconds()
        return (self.completed_at - self.started_at).total_seconds()
