"""Reference type model - Single source of truth for catalog data."""
from sqlalchemy import (
    Column, Integer, String, Numeric, DateTime, Text, JSON,
    UniqueConstraint, ForeignKey
)
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class ReferenceType(Base):
    """
    Catalog type record - single source of truth for reference data.
    
    One ReferenceType can be referenced by many CoinReferences.
    For example, "RIC I 207" is a type that multiple specimen coins can cite.
    """
    
    __tablename__ = "reference_types"
    
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Core identification (REQUIRED)
    system = Column(String(20), nullable=False, index=True)  # "ric", "crawford", "rpc"
    local_ref = Column(String(100), nullable=False)          # "RIC I 207", "Crawford 335/1c"
    local_ref_normalized = Column(String(100), nullable=False, unique=True, index=True)  # "ric.1.207"
    
    # Parsed components
    volume = Column(String(20))       # "I", "II", "1", etc.
    number = Column(String(50))       # "207", "335/1c"
    edition = Column(String(10))      # "2" for RIC I(2) second edition
    
    # External catalog link
    external_id = Column(String(100))         # "ric.1(2).aug.207" from OCRE/CRRO
    external_url = Column(String(500))        # Full URL to catalog page
    
    # Lookup metadata
    lookup_status = Column(String(20), default="pending")  # pending, success, not_found, ambiguous, deferred, error
    lookup_confidence = Column(Numeric(3, 2))              # 0.00-1.00 from reconciliation
    last_lookup = Column(DateTime)
    source_version = Column(String(50))                    # OCRE snapshot date for future-proofing
    error_message = Column(Text)                           # Last error if any
    
    # Cached catalog data
    payload = Column(JSON)                    # Parsed JSON-LD summary
    citation = Column(Text)                   # Generated catalog citation
    bibliography_refs = Column(JSON)          # Related bibliography from catalog
    
    # Relationships
    coin_references = relationship("CoinReference", back_populates="reference_type")
    match_attempts = relationship("ReferenceMatchAttempt", back_populates="reference_type")
    price_history = relationship("PriceHistory", back_populates="reference_type")
    
    def __repr__(self):
        return f"<ReferenceType {self.system}:{self.local_ref}>"


class ReferenceMatchAttempt(Base):
    """Audit log for catalog matching attempts."""
    
    __tablename__ = "reference_match_attempts"
    
    id = Column(Integer, primary_key=True)
    reference_type_id = Column(
        Integer,
        ForeignKey("reference_types.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    # Query details
    query_sent = Column(Text)                 # The actual query sent to API
    context_used = Column(JSON)               # Coin context used (ruler, mint, etc.)
    
    # Result
    result_status = Column(String(20))        # success, not_found, ambiguous, error
    confidence = Column(Numeric(3, 2))
    candidates_returned = Column(Integer)
    selected_candidate = Column(JSON)         # Which candidate was chosen
    error_message = Column(Text)
    
    # Relationship
    reference_type = relationship("ReferenceType", back_populates="match_attempts")
