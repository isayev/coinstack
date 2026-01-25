from sqlalchemy import String, Integer, Text, Boolean, DateTime, Enum, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import List, Optional
from datetime import datetime
from src.infrastructure.persistence.models import Base

class SeriesModel(Base):
    __tablename__ = "series"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    series_type: Mapped[str] = mapped_column(String(50), nullable=False)
    category: Mapped[Optional[str]] = mapped_column(String(50))
    
    target_count: Mapped[Optional[int]] = mapped_column(Integer)
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    completion_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # V3: Link to canonical series definition in vocab_terms
    canonical_vocab_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("vocab_terms.id"), nullable=True
    )
    
    # Relationships
    slots: Mapped[List["SeriesSlotModel"]] = relationship(back_populates="series", cascade="all, delete-orphan")
    memberships: Mapped[List["SeriesMembershipModel"]] = relationship(back_populates="series", cascade="all, delete-orphan")
    canonical_definition: Mapped[Optional["VocabTermModel"]] = relationship(
        "src.infrastructure.persistence.models_vocab.VocabTermModel"
    )

    __table_args__ = (
        CheckConstraint('target_count IS NULL OR target_count > 0', name='check_target_count'),
    )

class SeriesSlotModel(Base):
    __tablename__ = "series_slots"

    id: Mapped[int] = mapped_column(primary_key=True)
    series_id: Mapped[int] = mapped_column(ForeignKey("series.id", ondelete='CASCADE'), nullable=False)
    slot_number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    
    status: Mapped[str] = mapped_column(String(20), default="empty", index=True)
    
    priority: Mapped[int] = mapped_column(Integer, default=5)
    
    series: Mapped["SeriesModel"] = relationship(back_populates="slots")
    memberships: Mapped[List["SeriesMembershipModel"]] = relationship(back_populates="slot", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint('slot_number > 0', name='check_slot_number'),
        UniqueConstraint('series_id', 'slot_number', name='uq_series_slot_number'),
    )

class SeriesMembershipModel(Base):
    __tablename__ = "series_memberships"

    id: Mapped[int] = mapped_column(primary_key=True)
    series_id: Mapped[int] = mapped_column(ForeignKey("series.id", ondelete='CASCADE'), nullable=False)
    coin_id: Mapped[int] = mapped_column(ForeignKey("coins_v2.id", ondelete='CASCADE'), nullable=False)
    slot_id: Mapped[Optional[int]] = mapped_column(ForeignKey("series_slots.id", ondelete='SET NULL'))

    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    series: Mapped["SeriesModel"] = relationship(back_populates="memberships")
    slot: Mapped[Optional["SeriesSlotModel"]] = relationship(back_populates="memberships")
    # coin_rel: Mapped["CoinModel"] = relationship("src.infrastructure.persistence.orm.CoinModel") # Would need a circular import

