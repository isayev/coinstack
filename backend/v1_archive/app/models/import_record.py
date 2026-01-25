"""ImportRecord model - Tracks provenance of imported coins."""
from sqlalchemy import (
    Column, Integer, String, DateTime, JSON, ForeignKey, 
    UniqueConstraint, Index, Text
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class ImportSourceType(enum.Enum):
    """Import source types."""
    HERITAGE = "heritage"
    CNG = "cng"
    EBAY = "ebay"
    BIDDR = "biddr"
    ROMA = "roma"
    AGORA = "agora"
    NGC = "ngc"
    PCGS = "pcgs"
    VCOINS = "vcoins"
    MA_SHOPS = "ma_shops"
    FILE = "file"           # Excel/CSV import
    MANUAL = "manual"       # Manual entry


class ImportRecord(Base):
    """
    Tracks the provenance of imported coins.
    
    Stores the original source information for every imported coin,
    enabling duplicate detection, debugging, and audit trails.
    """
    
    __tablename__ = "import_records"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Link to coin
    coin_id = Column(Integer, ForeignKey("coins.id", ondelete="CASCADE"), nullable=False)
    
    # Source identification
    source_type = Column(String(50), nullable=False, index=True)  # heritage, cng, ngc, ebay, file, manual
    source_id = Column(String(100), index=True)  # Lot ID, cert number, etc. e.g., "61519-25289"
    source_url = Column(String(500))  # Full URL to original listing
    
    # Timestamps
    imported_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Raw data for debugging and re-parsing
    raw_data = Column(JSON)  # Original scraped JSON
    
    # Import metadata
    import_method = Column(String(50))  # "url_scrape", "ngc_lookup", "file_upload", "manual"
    imported_by = Column(String(100))  # User identifier if multi-user
    
    # For file imports
    file_name = Column(String(255))
    file_row = Column(Integer)
    
    # Enrichment tracking
    enriched_at = Column(DateTime)
    enrichment_source = Column(String(50))  # ocre, crro, rpc
    
    # Relationships
    coin = relationship("Coin", back_populates="import_record")
    
    # Constraints
    __table_args__ = (
        # Unique constraint to prevent duplicate imports from same source
        UniqueConstraint('source_type', 'source_id', name='uq_import_source'),
        # Index for fast duplicate lookups
        Index('ix_import_source_lookup', 'source_type', 'source_id'),
    )
    
    def __repr__(self):
        return f"<ImportRecord(id={self.id}, source={self.source_type}:{self.source_id}, coin_id={self.coin_id})>"
