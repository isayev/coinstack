from sqlalchemy import String, Integer, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from src.infrastructure.persistence.models import Base

class IssuerModel(Base):
    __tablename__ = "issuers"

    id: Mapped[int] = mapped_column(primary_key=True)
    canonical_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    nomisma_id: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    issuer_type: Mapped[str] = mapped_column(String(20))
    reign_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reign_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    __table_args__ = (
        CheckConstraint('reign_start <= reign_end', name='check_reign_dates'),
    )

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
