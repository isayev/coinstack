"""
Vocabulary ORM Models (V3)

This module defines the SQLAlchemy ORM models for the unified controlled vocabulary system.
"""

from sqlalchemy import String, Integer, Text, Float, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional
from src.infrastructure.persistence.models import Base


class VocabTermModel(Base):
    """
    Unified vocabulary term ORM model.
    
    Stores all vocabulary types (issuer, mint, denomination, dynasty, canonical_series)
    in a single table with type discrimination via vocab_type column.
    
    The metadata column stores type-specific JSON data.
    """
    __tablename__ = "vocab_terms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vocab_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    canonical_name: Mapped[str] = mapped_column(String(200), nullable=False)
    nomisma_uri: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    # Note: 'metadata' is reserved by SQLAlchemy, so we use 'term_metadata' as attribute name
    # but map to 'metadata' column in the database
    term_metadata: Mapped[Optional[str]] = mapped_column("metadata", Text, nullable=True)  # JSON string
    created_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)


class CoinVocabAssignmentModel(Base):
    """
    Audit trail for vocabulary assignments to coins.
    
    Tracks which vocabulary terms have been assigned to which coins,
    along with the method used (exact, fts, nomisma, manual) and confidence score.
    Items with status='pending_review' are shown in the review queue.
    """
    __tablename__ = "coin_vocab_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    coin_id: Mapped[int] = mapped_column(Integer, ForeignKey("coins_v2.id"), nullable=False, index=True)
    field_name: Mapped[str] = mapped_column(String(50), nullable=False)  # 'issuer', 'mint', etc.
    raw_value: Mapped[str] = mapped_column(Text, nullable=False)
    vocab_term_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("vocab_terms.id"), nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # 'exact', 'fts', 'nomisma', 'llm', 'manual'
    status: Mapped[str] = mapped_column(String(20), default="assigned", index=True)  # 'assigned', 'pending_review', 'approved', 'rejected'
    assigned_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reviewed_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Relationships
    vocab_term: Mapped[Optional["VocabTermModel"]] = relationship("VocabTermModel")


class VocabCacheModel(Base):
    """
    Simple key-value cache for vocabulary operations.
    
    Used to cache search results (1hr TTL) and external API responses (1yr TTL).
    """
    __tablename__ = "vocab_cache"
    
    cache_key: Mapped[str] = mapped_column(String(200), primary_key=True)
    data: Mapped[str] = mapped_column(Text, nullable=False)
    expires_at: Mapped[str] = mapped_column(String(50), nullable=False, index=True)


# Legacy models (deprecated but kept for backward compatibility)

class IssuerModel(Base):
    """
    Legacy Issuer ORM model (deprecated).
    
    Use VocabTermModel with vocab_type='issuer' instead.
    This model is kept for backward compatibility during migration.
    """
    __tablename__ = "issuers"

    id: Mapped[int] = mapped_column(primary_key=True)
    canonical_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    nomisma_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    issuer_type: Mapped[str] = mapped_column(String(20))
    reign_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reign_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    aliases: Mapped[list["IssuerAliasModel"]] = relationship(back_populates="issuer", cascade="all, delete-orphan")


class IssuerAliasModel(Base):
    """
    Legacy Issuer Alias ORM model (deprecated).
    
    The V3 system uses FTS5 full-text search instead of explicit aliases.
    """
    __tablename__ = "issuer_aliases"

    id: Mapped[int] = mapped_column(primary_key=True)
    issuer_id: Mapped[int] = mapped_column(ForeignKey("issuers.id"), nullable=False)
    alias: Mapped[str] = mapped_column(String(200), nullable=False)
    normalized_form: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    
    issuer: Mapped["IssuerModel"] = relationship(back_populates="aliases")


class MintModel(Base):
    """
    Legacy Mint ORM model (deprecated).
    
    Use VocabTermModel with vocab_type='mint' instead.
    """
    __tablename__ = "mints"

    id: Mapped[int] = mapped_column(primary_key=True)
    canonical_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    nomisma_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    active_from: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    active_to: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
