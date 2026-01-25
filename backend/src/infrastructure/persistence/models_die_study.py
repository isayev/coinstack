"""
Die Study ORM Models.

SQLAlchemy models for persisting die links and die study groups.
"""

from typing import Optional
from datetime import datetime
from sqlalchemy import Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column

from src.infrastructure.persistence.models import Base


class DieLinkModel(Base):
    """
    ORM model for die links between coins.
    
    Represents that two coins share the same die on one side.
    Unique constraint prevents duplicate links.
    """
    __tablename__ = "die_links"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # The two coins in the link
    coin_a_id: Mapped[int] = mapped_column(Integer, ForeignKey("coins_v2.id"), index=True)
    coin_b_id: Mapped[int] = mapped_column(Integer, ForeignKey("coins_v2.id"), index=True)
    
    # Which side shares the die
    die_side: Mapped[str] = mapped_column(String(20))  # "obverse" or "reverse"
    
    # Confidence and source
    confidence: Mapped[str] = mapped_column(String(20))  # certain, probable, possible, uncertain
    source: Mapped[str] = mapped_column(String(20), default="manual")  # manual, llm, reference, import
    
    # Additional info
    reference: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Timestamps
    identified_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Prevent duplicate links (same pair, same side)
    __table_args__ = (
        UniqueConstraint('coin_a_id', 'coin_b_id', 'die_side', name='uq_die_link_pair_side'),
    )


class DieStudyGroupModel(Base):
    """
    ORM model for die study groups.
    
    A group of coins that share a single die.
    """
    __tablename__ = "die_groups"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    # Group identity
    name: Mapped[str] = mapped_column(String(100))
    die_side: Mapped[str] = mapped_column(String(20))  # "obverse" or "reverse"
    
    # Associated issuer/mint (for filtering)
    issuer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("issuers.id"), nullable=True)
    mint_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("mints.id"), nullable=True)
    
    # Description
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # Relationship to members
    members: Mapped[list["DieGroupMemberModel"]] = relationship(
        back_populates="group", 
        cascade="all, delete-orphan"
    )


class DieGroupMemberModel(Base):
    """
    Junction table linking coins to die study groups.
    
    Includes sequence_position for tracking estimated strike order.
    """
    __tablename__ = "die_group_members"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    
    die_group_id: Mapped[int] = mapped_column(Integer, ForeignKey("die_groups.id"), index=True)
    coin_id: Mapped[int] = mapped_column(Integer, ForeignKey("coins_v2.id"), index=True)
    
    # Estimated strike order within the group (1 = earliest, higher = later)
    sequence_position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # Relationship
    group: Mapped["DieStudyGroupModel"] = relationship(back_populates="members")
    
    # Prevent duplicate memberships
    __table_args__ = (
        UniqueConstraint('die_group_id', 'coin_id', name='uq_die_group_member'),
    )
