from sqlalchemy import String, Integer, CheckConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from src.infrastructure.persistence.models import Base

class IssuerModel(Base):
    __tablename__ = "issuers"

    id: Mapped[int] = mapped_column(primary_key=True)
    canonical_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    nomisma_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    issuer_type: Mapped[str] = mapped_column(String(20))
    reign_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reign_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    aliases: Mapped[List["IssuerAliasModel"]] = relationship(back_populates="issuer", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint('reign_start <= reign_end', name='check_reign_dates'),
    )

class IssuerAliasModel(Base):
    __tablename__ = "issuer_aliases"

    id: Mapped[int] = mapped_column(primary_key=True)
    issuer_id: Mapped[int] = mapped_column(ForeignKey("issuers.id"), nullable=False)
    alias: Mapped[str] = mapped_column(String(200), nullable=False)
    normalized_form: Mapped[str] = mapped_column(String(200), index=True, nullable=False)
    
    issuer: Mapped["IssuerModel"] = relationship(back_populates="aliases")

class MintModel(Base):
    __tablename__ = "mints"

    id: Mapped[int] = mapped_column(primary_key=True)
    canonical_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    nomisma_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    active_from: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    active_to: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        CheckConstraint('active_from <= active_to', name='check_active_dates'),
    )