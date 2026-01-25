from typing import Optional, List
from decimal import Decimal
from datetime import date, datetime
from sqlalchemy import Integer, String, Numeric, Date, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from src.infrastructure.persistence.models import Base

class CoinModel(Base):
    __tablename__ = "coins_v2"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Category/Metal (indexed for filtering)
    category: Mapped[str] = mapped_column(String, index=True)
    metal: Mapped[str] = mapped_column(String, index=True)

    # Dimensions (Embedded)
    weight_g: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    diameter_mm: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    die_axis: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Attribution (Embedded)
    issuer: Mapped[str] = mapped_column(String)
    issuer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("issuers.id"), nullable=True)
    mint: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    mint_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("mints.id"), nullable=True)
    year_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    year_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # V3 Vocab FKs (unified vocabulary system)
    issuer_term_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("vocab_terms.id"), nullable=True)
    mint_term_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("vocab_terms.id"), nullable=True)
    denomination_term_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("vocab_terms.id"), nullable=True)
    dynasty_term_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("vocab_terms.id"), nullable=True)

    # Grading (Embedded)
    grading_state: Mapped[str] = mapped_column(String, index=True)
    grade: Mapped[str] = mapped_column(String)
    grade_service: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    certification_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    strike_quality: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    surface_quality: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Acquisition (Embedded - Optional)
    acquisition_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    acquisition_currency: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    acquisition_source: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    acquisition_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    acquisition_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Description
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Denomination and Portrait Subject (from expert review)
    denomination: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    portrait_subject: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Design fields (obverse/reverse legends and descriptions)
    obverse_legend: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    obverse_description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    reverse_legend: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    reverse_description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    exergue: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # -------------------------------------------------------------------------
    # LLM-Generated Fields (Phase 1C)
    # -------------------------------------------------------------------------
    # Expanded legends (from legend_expand capability)
    obverse_legend_expanded: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    reverse_legend_expanded: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Historical context narrative (from context_generate capability)
    historical_significance: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Catalog-style description (from description_generate capability)
    catalog_description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Condition observations (from condition_observations capability - JSON string)
    # Contains: wear_observations, surface_notes, strike_quality, notable_features
    condition_observations: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # LLM enrichment metadata
    llm_enriched_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # Collection management fields (migrated from V1)
    storage_location: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    personal_notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationships
    images: Mapped[List["CoinImageModel"]] = relationship(back_populates="coin", cascade="all, delete-orphan")
    auction_data: Mapped[Optional["AuctionDataModel"]] = relationship(back_populates="coin", uselist=False)
    references: Mapped[List["CoinReferenceModel"]] = relationship(back_populates="coin", cascade="all, delete-orphan")
    provenance_events: Mapped[List["ProvenanceEventModel"]] = relationship(back_populates="coin", cascade="all, delete-orphan")
    
    # Legacy vocab relationships (deprecated)
    issuer_rel: Mapped[Optional["IssuerModel"]] = relationship("src.infrastructure.persistence.models_vocab.IssuerModel")
    mint_rel: Mapped[Optional["MintModel"]] = relationship("src.infrastructure.persistence.models_vocab.MintModel")
    
    # V3 Vocab relationships (unified vocabulary system)
    issuer_vocab: Mapped[Optional["VocabTermModel"]] = relationship(
        "src.infrastructure.persistence.models_vocab.VocabTermModel",
        foreign_keys=[issuer_term_id]
    )
    mint_vocab: Mapped[Optional["VocabTermModel"]] = relationship(
        "src.infrastructure.persistence.models_vocab.VocabTermModel",
        foreign_keys=[mint_term_id]
    )
    denomination_vocab: Mapped[Optional["VocabTermModel"]] = relationship(
        "src.infrastructure.persistence.models_vocab.VocabTermModel",
        foreign_keys=[denomination_term_id]
    )
    dynasty_vocab: Mapped[Optional["VocabTermModel"]] = relationship(
        "src.infrastructure.persistence.models_vocab.VocabTermModel",
        foreign_keys=[dynasty_term_id]
    )

class CoinImageModel(Base):
    __tablename__ = "coin_images_v2"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    coin_id: Mapped[int] = mapped_column(Integer, ForeignKey("coins_v2.id"))
    url: Mapped[str] = mapped_column(String)
    image_type: Mapped[str] = mapped_column(String)  # obverse, reverse
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    coin: Mapped["CoinModel"] = relationship(back_populates="images")

class AuctionDataModel(Base):
    __tablename__ = "auction_data_v2"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    coin_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("coins_v2.id"), nullable=True)

    # URL is unique key
    url: Mapped[str] = mapped_column(String, unique=True, index=True)
    source: Mapped[str] = mapped_column(String)  # e.g. "Heritage", "CNG"
    sale_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    lot_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    source_lot_id: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Financials
    hammer_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    estimate_low: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    estimate_high: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Attribution from Scraper
    issuer: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    mint: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    year_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    year_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Physical
    weight_g: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), nullable=True)
    diameter_mm: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    die_axis: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Descriptions
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Grading
    grade: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Images (JSON list of URLs)
    primary_image_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    additional_images: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Stored as JSON string

    # Metadata
    scraped_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    coin: Mapped[Optional["CoinModel"]] = relationship(back_populates="auction_data")


class CoinReferenceModel(Base):
    """
    Links coins to catalog reference types (RIC, Crawford, Sear, etc.)
    
    Note: This model is compatible with the existing V1 schema which uses
    a separate reference_types table for the actual catalog data.
    """
    __tablename__ = "coin_references"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    coin_id: Mapped[int] = mapped_column(Integer, ForeignKey("coins_v2.id"), index=True)
    
    # Link to reference_types table (V1 schema)
    reference_type_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("reference_types.id"), nullable=True, index=True)
    
    # Specimen-specific fields
    is_primary: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=False)
    plate_coin: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=False)
    position: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # "obverse", "reverse", "both"
    variant_notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Citation fields
    page: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    plate: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    note_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    coin: Mapped["CoinModel"] = relationship(back_populates="references")


class ProvenanceEventModel(Base):
    """
    Provenance events tracking coin ownership history.
    
    Records auction appearances, collection holdings, dealer sales, etc.
    Compatible with V1 schema structure.
    """
    __tablename__ = "provenance_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    coin_id: Mapped[int] = mapped_column(Integer, ForeignKey("coins_v2.id"), index=True)
    
    # Event classification
    event_type: Mapped[str] = mapped_column(String(50))  # "auction", "dealer", "collection", "private_sale", etc.
    event_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Auction details
    auction_house: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sale_series: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    sale_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    lot_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    catalog_reference: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    
    # Pricing
    hammer_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    buyers_premium_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(4, 2), nullable=True)
    total_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    
    # Dealer/Collection details
    dealer_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    collection_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Documentation
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    receipt_available: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=False)
    notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    sort_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, default=0)
    
    # Link to auction_data if from tracked scrape
    auction_data_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("auction_data_v2.id"), nullable=True)
    
    coin: Mapped["CoinModel"] = relationship(back_populates="provenance_events")
