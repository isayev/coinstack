from typing import Optional, List
from decimal import Decimal
from datetime import date, datetime
from sqlalchemy import Integer, String, Text, Numeric, Date, DateTime, Boolean, ForeignKey, Table, Column, CheckConstraint
from sqlalchemy.orm import relationship, Mapped, mapped_column
from src.infrastructure.persistence.models import Base

# Association Table for Monograms (Many-to-Many)
coin_monograms = Table(
    "coin_monograms",
    Base.metadata,
    Column("coin_id", Integer, ForeignKey("coins_v2.id"), primary_key=True),
    Column("monogram_id", Integer, ForeignKey("monograms.id"), primary_key=True),
)

class MonogramModel(Base):
    __tablename__ = "monograms"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    label: Mapped[str] = mapped_column(String(100), index=True) # e.g. "Price 123"
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    vector_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # SVG path or data
    
    # Relationship back to coins
    coins: Mapped[List["CoinModel"]] = relationship(secondary=coin_monograms, back_populates="monograms")

class CoinModel(Base):
    __tablename__ = "coins_v2"
    
    # Check constraints
    __table_args__ = (
        CheckConstraint('die_axis >= 0 AND die_axis <= 12', name='check_die_axis_range'),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Category/Metal (indexed for filtering)
    category: Mapped[str] = mapped_column(String(50), index=True)
    metal: Mapped[str] = mapped_column(String(50), index=True)

    # Dimensions (Embedded); weight_g optional (e.g. slabbed coins cannot be weighed)
    # UPDATED: Precision 10,3 for accurate numismatic weights
    weight_g: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), nullable=True)
    diameter_mm: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    die_axis: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Attribution (Embedded)
    issuer: Mapped[str] = mapped_column(String(100))
    issuer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("issuers.id"), nullable=True)
    mint: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    mint_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("mints.id"), nullable=True)
    year_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    year_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # V3 Vocab FKs (unified vocabulary system)
    issuer_term_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("vocab_terms.id"), nullable=True)
    mint_term_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("vocab_terms.id"), nullable=True)
    denomination_term_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("vocab_terms.id"), nullable=True)
    dynasty_term_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("vocab_terms.id"), nullable=True)

    # Grading (Embedded)
    grading_state: Mapped[str] = mapped_column(String(20), index=True)
    grade: Mapped[str] = mapped_column(String(20))
    grade_service: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    certification_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    strike_quality: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    surface_quality: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Acquisition (Embedded - Optional)
    acquisition_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    acquisition_currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    acquisition_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    acquisition_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    acquisition_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Description
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Denomination and Portrait Subject (from expert review)
    # UPDATED: Added indexes for common filters
    denomination: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    portrait_subject: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    
    # Design fields (obverse/reverse legends and descriptions)
    obverse_legend: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    obverse_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    reverse_legend: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    reverse_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    exergue: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # -------------------------------------------------------------------------
    # Research Grade Extensions (V2.1)
    # -------------------------------------------------------------------------
    
    # Production & Authenticity
    issue_status: Mapped[str] = mapped_column(String(20), default="official", index=True) 
    # Values: 'official', 'fourree', 'imitation', 'barbarous', 'modern_fake'
    
    # Metrology
    specific_gravity: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    
    # Die Linking
    obverse_die_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    reverse_die_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    
    # Structured Secondary Treatments (Countermarks, bankers marks, etc - JSON)
    secondary_treatments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Find Data
    find_spot: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    find_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # -------------------------------------------------------------------------
    # LLM-Generated Fields (Phase 1C)
    # -------------------------------------------------------------------------
    # Expanded legends (from legend_expand capability)
    obverse_legend_expanded: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reverse_legend_expanded: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Historical context narrative (from context_generate capability)
    historical_significance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Catalog-style description (from description_generate capability)
    catalog_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Condition observations (from condition_observations capability - JSON string)
    # Contains: wear_observations, surface_notes, strike_quality, notable_features
    condition_observations: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # LLM enrichment metadata
    llm_enriched_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    llm_analysis_sections: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON string of sections
    llm_suggested_references: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array of suggested refs not in DB
    llm_suggested_rarity: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON object with rarity info from LLM
    llm_suggested_design: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON: obverse_legend, reverse_legend, exergue, obverse_description, reverse_description, *_expanded
    llm_suggested_attribution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON: issuer, mint, denomination, year_start, year_end

    # Collection management fields (migrated from V1)
    storage_location: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    personal_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # -------------------------------------------------------------------------
    # Additional V1 fields (restored from migration)
    # -------------------------------------------------------------------------
    # Script/Language
    script: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Latin, Greek, etc.
    
    # Chronology (ruler reign dates)
    reign_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Year (negative for BC)
    reign_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    dating_certainty: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # BROAD, NARROW, EXACT
    is_circa: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=False)
    
    # Provenance and history
    provenance_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Auction/collection history
    
    # Physical characteristics
    surface_issues: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array of issues
    thickness_mm: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    orientation: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Classification
    series: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sub_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Mint details
    officina: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # Mint workshop
    
    # Design symbols
    obverse_symbols: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reverse_symbols: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # Rarity and value
    rarity: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    rarity_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Condition notes
    style_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    toning_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    eye_appeal: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # -------------------------------------------------------------------------
    # Advanced Numismatic Fields (Phase 2 - Comprehensive Cataloging)
    # -------------------------------------------------------------------------
    
    # Iconography and design details (JSON arrays stored as strings)
    obverse_iconography: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array of design elements
    reverse_iconography: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array of design elements
    control_marks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array of control marks
    
    # Mint marks and control symbols
    mintmark: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Specific mint mark on coin
    field_marks: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Symbols in field (JSON array)
    
    # Die study fields (complement existing die_axis)
    die_state: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # early, middle, late, worn
    die_match_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Notes about die matches
    
    # Republican coinage specific
    moneyer: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Moneyer name for Republican coins
    
    # Edge details
    edge_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)  # plain, reeded, lettered, decorated
    edge_inscription: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Edge lettering if present
    
    # Attribution confidence
    attribution_confidence: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # certain, probable, possible, uncertain
    attribution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Notes on attribution
    
    # Conservation and cleaning history
    cleaning_history: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Previous cleaning/conservation
    conservation_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Conservation work done
    
    # Market value tracking
    market_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)  # Current market estimate
    market_value_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)  # Date of valuation

    # -------------------------------------------------------------------------
    # Schema V3 - Phase 1: Core Numismatic Enhancements
    # -------------------------------------------------------------------------

    # Attribution enhancements
    secondary_authority: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    secondary_authority_term_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("vocab_terms.id"), nullable=True)
    authority_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    # authority_type values: 'magistrate', 'satrap', 'dynast', 'strategos', 'archon', 'epistates'

    co_ruler: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    co_ruler_term_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("vocab_terms.id"), nullable=True)
    portrait_relationship: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    # portrait_relationship: 'self', 'consort', 'heir', 'parent', 'predecessor', 'commemorative', 'divus', 'diva'

    moneyer_gens: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Physical enhancements
    weight_standard: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # weight_standard: 'attic', 'aeginetan', 'corinthian', 'phoenician', 'denarius_early', etc.
    expected_weight_g: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), nullable=True)
    flan_shape: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    # flan_shape: 'round', 'irregular', 'oval', 'square', 'scyphate'
    flan_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    # flan_type: 'cast', 'struck', 'cut_from_bar', 'hammered'
    flan_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Secondary treatments (structured)
    is_overstrike: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, index=True)
    undertype_visible: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    undertype_attribution: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    has_test_cut: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    test_cut_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    test_cut_positions: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    has_bankers_marks: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    has_graffiti: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    graffiti_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    was_mounted: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    mount_evidence: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Tooling/repairs
    tooling_extent: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    # tooling_extent: 'none', 'minor', 'moderate', 'significant', 'extensive'
    tooling_details: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    has_ancient_repair: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    ancient_repairs: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Centering
    centering: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    # centering: 'well-centered', 'slightly_off', 'off_center', 'significantly_off'
    centering_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Die study enhancements (per-side states)
    obverse_die_state: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    reverse_die_state: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    # die state: 'fresh', 'early', 'middle', 'late', 'worn', 'broken', 'repaired'
    die_break_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Grading TPG enhancements
    grade_numeric: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    # NGC/PCGS numeric: 50, 53, 55, 58, 60, 62, 63, 64, 65, 66, 67, 68, 69, 70
    grade_designation: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # grade_designation: 'Fine Style', 'Choice', 'Gem', 'Superb Gem'
    has_star_designation: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, index=True)
    photo_certificate: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    verification_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Chronology enhancements
    date_period_notation: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # Human-readable: "c. 150-100 BC", "late 3rd century AD"
    emission_phase: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # emission_phase: 'First Issue', 'Second Issue', 'Reform Coinage', 'Heavy Series', 'Light Series'

    # Relationships
    images: Mapped[List["CoinImageModel"]] = relationship(back_populates="coin", cascade="all, delete-orphan")
    # UPDATED: Added cascade to prevent orphaned auction data
    auction_data: Mapped[Optional["AuctionDataModel"]] = relationship(back_populates="coin", uselist=False, cascade="all, delete-orphan")
    references: Mapped[List["CoinReferenceModel"]] = relationship(back_populates="coin", cascade="all, delete-orphan")
    provenance_events: Mapped[List["ProvenanceEventModel"]] = relationship(back_populates="coin", cascade="all, delete-orphan")
    monograms: Mapped[List["MonogramModel"]] = relationship(secondary=coin_monograms, back_populates="coins")
    
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
    url: Mapped[str] = mapped_column(String(500))
    image_type: Mapped[str] = mapped_column(String(20))  # obverse, reverse
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    coin: Mapped["CoinModel"] = relationship(back_populates="images")

class AuctionDataModel(Base):
    __tablename__ = "auction_data_v2"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    coin_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("coins_v2.id"), nullable=True)

    # URL is unique key
    url: Mapped[str] = mapped_column(String(500), unique=True, index=True)
    source: Mapped[str] = mapped_column(String(100))  # e.g. "Heritage", "CNG"
    sale_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    lot_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    source_lot_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Financials
    hammer_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    estimate_low: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    estimate_high: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)

    # Attribution from Scraper
    issuer: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    mint: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    year_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    year_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Physical
    weight_g: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), nullable=True)
    diameter_mm: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    die_axis: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Descriptions
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Grading
    grade: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Images (JSON list of URLs)
    primary_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    additional_images: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Stored as JSON string

    # Metadata
    scraped_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    coin: Mapped[Optional["CoinModel"]] = relationship(back_populates="auction_data")


class ReferenceTypeModel(Base):
    """
    Catalog reference types (RIC, Crawford, Sear, etc.)
    
    This is a V1 schema table that stores the actual catalog metadata.
    Each reference_type is a unique catalog + number combination.
    """
    __tablename__ = "reference_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    system: Mapped[str] = mapped_column(String(20))  # ric, crawford, sear, rpc, etc.
    local_ref: Mapped[str] = mapped_column(String(100))  # canonical form e.g. "RIC I 207"
    local_ref_normalized: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    volume: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # Roman for RIC/RPC
    number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # "207", "335/1c"
    external_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    external_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    # Optional catalog-specific (backward compatible; add columns with NULL for existing DBs)
    variant: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)   # e.g. "a", "b"
    mint: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)       # RIC mint code
    supplement: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # RPC S, S2
    collection: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # SNG collection

    # Relationships
    coin_references: Mapped[List["CoinReferenceModel"]] = relationship(back_populates="reference_type")


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
    
    # Origin of this link: "user" | "import" | "scraper" | "llm_approved" | "catalog_lookup"
    source: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, index=True)
    
    # Relationships
    coin: Mapped["CoinModel"] = relationship(back_populates="references")
    reference_type: Mapped[Optional["ReferenceTypeModel"]] = relationship(back_populates="coin_references")


class ProvenanceEventModel(Base):
    """
    Provenance events tracking coin ownership history (V3 schema).

    Records auction appearances, collection holdings, dealer sales, etc.
    Uses unified source_name field instead of separate auction_house/dealer_name/collection_name.

    The ACQUISITION event_type represents current ownership (final pedigree entry).
    """
    __tablename__ = "provenance_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    coin_id: Mapped[int] = mapped_column(Integer, ForeignKey("coins_v2.id"), index=True)

    # Event classification - UNIFIED source field (V3)
    event_type: Mapped[str] = mapped_column(String(50), index=True)  # ProvenanceEventType enum value
    source_name: Mapped[str] = mapped_column(String(200), nullable=False, default="", index=True)  # Unified!

    # Dating (flexible)
    event_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    date_string: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # "1920s", "circa 1840"

    # Auction/Sale details
    sale_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # "January 2024 NYINC Sale"
    sale_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Catalog number
    lot_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    catalog_reference: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Pricing
    hammer_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    buyers_premium_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    total_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)  # ISO 4217

    # Documentation
    url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    receipt_available: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Metadata
    source_origin: Mapped[str] = mapped_column(String(30), nullable=False, default="manual_entry", index=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, index=True)

    # Link to auction_data if from tracked scrape
    auction_data_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("auction_data_v2.id"), nullable=True, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, onupdate=datetime.utcnow)

    # --- LEGACY FIELDS (kept for migration, will be removed in future) ---
    auction_house: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    dealer_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    collection_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sale_series: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Legacy, use sale_name

    # Relationships
    coin: Mapped["CoinModel"] = relationship(back_populates="provenance_events")


class EnrichmentJobModel(Base):
    """
    Tracks bulk catalog enrichment job progress and results.
    Used by POST /api/catalog/bulk-enrich and GET /api/catalog/job/{id}.
    """
    __tablename__ = "enrichment_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)  # UUID
    status: Mapped[str] = mapped_column(String(20), index=True)  # queued, running, completed, failed
    total: Mapped[int] = mapped_column(Integer, default=0)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    updated: Mapped[int] = mapped_column(Integer, default=0)
    conflicts: Mapped[int] = mapped_column(Integer, default=0)
    not_found: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[int] = mapped_column(Integer, default=0)
    result_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)


# =============================================================================
# Schema V3 - Phase 2: Grading & Rarity System
# =============================================================================

class GradingHistoryModel(Base):
    """Track complete grading lifecycle (raw → slabbed → regraded)."""
    __tablename__ = "grading_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    coin_id: Mapped[int] = mapped_column(Integer, ForeignKey("coins_v2.id", ondelete="CASCADE"), index=True)

    # Grading state at this point
    grading_state: Mapped[str] = mapped_column(String(20), nullable=False)
    grade: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    grade_service: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    certification_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    strike_quality: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    surface_quality: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    grade_numeric: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    designation: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    has_star: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    photo_cert: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    verification_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Event tracking
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    graded_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    submitter: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    turnaround_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    grading_fee: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Ordering
    sequence_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_current: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Relationship
    coin: Mapped["CoinModel"] = relationship("CoinModel", backref="grading_history_entries")


class RarityAssessmentModel(Base):
    """Multi-source rarity tracking with grade-conditional support."""
    __tablename__ = "rarity_assessments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    coin_id: Mapped[int] = mapped_column(Integer, ForeignKey("coins_v2.id", ondelete="CASCADE"), index=True)

    rarity_code: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    rarity_system: Mapped[str] = mapped_column(String(30), nullable=False)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False)
    source_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    source_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    source_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    grade_range_low: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    grade_range_high: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    grade_conditional_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    census_total: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    census_this_grade: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    census_finer: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    census_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    confidence: Mapped[Optional[str]] = mapped_column(String(20), default="medium")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_primary: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    coin: Mapped["CoinModel"] = relationship("CoinModel", backref="rarity_assessments")


class CensusSnapshotModel(Base):
    """Track NGC/PCGS population over time."""
    __tablename__ = "census_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    coin_id: Mapped[int] = mapped_column(Integer, ForeignKey("coins_v2.id", ondelete="CASCADE"), index=True)

    service: Mapped[str] = mapped_column(String(20), nullable=False)
    snapshot_date: Mapped[date] = mapped_column(Date, nullable=False)
    total_graded: Mapped[int] = mapped_column(Integer, nullable=False)
    grade_breakdown: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    coins_at_grade: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    coins_finer: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    percentile: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    catalog_reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    coin: Mapped["CoinModel"] = relationship("CoinModel", backref="census_snapshots")


# =============================================================================
# Schema V3 - Phase 3: Reference System Enhancements
# =============================================================================

class ReferenceConcordanceModel(Base):
    """Cross-reference linking (RIC 207 = RSC 112 = BMC 298)."""
    __tablename__ = "reference_concordance"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    concordance_group_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    reference_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("reference_types.id", ondelete="CASCADE"), index=True)
    confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), default=1.0)
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    reference_type: Mapped["ReferenceTypeModel"] = relationship("ReferenceTypeModel", backref="concordances")


class ExternalCatalogLinkModel(Base):
    """Links to OCRE, Nomisma, CRRO, RPC Online."""
    __tablename__ = "external_catalog_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    reference_type_id: Mapped[int] = mapped_column(Integer, ForeignKey("reference_types.id", ondelete="CASCADE"), index=True)
    catalog_source: Mapped[str] = mapped_column(String(30), nullable=False)
    external_id: Mapped[str] = mapped_column(String(100), nullable=False)
    external_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    external_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_synced_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    sync_status: Mapped[Optional[str]] = mapped_column(String(20), default="pending")

    reference_type: Mapped["ReferenceTypeModel"] = relationship("ReferenceTypeModel", backref="external_links")


# =============================================================================
# Schema V3 - Phase 4: LLM Architecture
# =============================================================================

class LLMEnrichmentModel(Base):
    """Centralized LLM enrichments with versioning and review workflow."""
    __tablename__ = "llm_enrichments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    coin_id: Mapped[int] = mapped_column(Integer, ForeignKey("coins_v2.id", ondelete="CASCADE"), index=True)

    capability: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    capability_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    model_id: Mapped[str] = mapped_column(String(50), nullable=False)
    model_version: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    input_hash: Mapped[str] = mapped_column(String(64), nullable=False)
    input_snapshot: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    output_content: Mapped[str] = mapped_column(Text, nullable=False)
    raw_response: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    confidence: Mapped[Decimal] = mapped_column(Numeric(3, 2), nullable=False)
    needs_review: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, index=True)
    quality_flags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    cost_usd: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 6), default=0)
    input_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    cached: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    latency_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    review_status: Mapped[Optional[str]] = mapped_column(String(20), default="pending", index=True)
    reviewed_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    superseded_by: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("llm_enrichments.id"), nullable=True)
    request_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    batch_job_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    coin: Mapped["CoinModel"] = relationship("CoinModel", backref="llm_enrichments")


class LLMPromptTemplateModel(Base):
    """Database-managed prompts for versioning and A/B testing."""
    __tablename__ = "llm_prompt_templates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    capability: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    version: Mapped[int] = mapped_column(Integer, nullable=False)

    system_prompt: Mapped[str] = mapped_column(Text, nullable=False)
    user_template: Mapped[str] = mapped_column(Text, nullable=False)
    parameters: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    requires_vision: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    preferred_model: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    max_tokens: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    temperature: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), nullable=True)
    output_schema: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    variant_name: Mapped[Optional[str]] = mapped_column(String(50), default="default")
    traffic_weight: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), default=1.0)

    is_active: Mapped[Optional[bool]] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    deprecated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class LLMFeedbackModel(Base):
    """Quality feedback loop for LLM enrichments."""
    __tablename__ = "llm_feedback"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    enrichment_id: Mapped[int] = mapped_column(Integer, ForeignKey("llm_enrichments.id", ondelete="CASCADE"), index=True)

    feedback_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    field_path: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    original_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    corrected_value: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    helpful: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    feedback_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    enrichment: Mapped["LLMEnrichmentModel"] = relationship("LLMEnrichmentModel", backref="feedback")


class LLMUsageDailyModel(Base):
    """Aggregated LLM analytics."""
    __tablename__ = "llm_usage_daily"

    date: Mapped[str] = mapped_column(String(10), primary_key=True)
    capability: Mapped[str] = mapped_column(String(50), primary_key=True)
    model_id: Mapped[str] = mapped_column(String(50), primary_key=True)

    request_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    cache_hits: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    error_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    total_cost_usd: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 4), default=0)
    total_input_tokens: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    total_output_tokens: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    avg_confidence: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), nullable=True)
    review_approved: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    review_rejected: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    avg_rating: Mapped[Optional[Decimal]] = mapped_column(Numeric(2, 1), nullable=True)
    avg_latency_ms: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    p95_latency_ms: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)


# =============================================================================
# Schema V3 - Phase 5: Market Tracking & Wishlists
# =============================================================================

class MarketPriceModel(Base):
    """Aggregate pricing by attribution."""
    __tablename__ = "market_prices"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    attribution_key: Mapped[str] = mapped_column(String(200), nullable=False, unique=True, index=True)

    issuer: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    denomination: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    mint: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    metal: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    catalog_ref: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    avg_price_vf: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    avg_price_ef: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    avg_price_au: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    min_price_seen: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    max_price_seen: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    median_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)

    data_point_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    last_sale_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    last_updated: Mapped[Optional[datetime]] = mapped_column(DateTime, default=datetime.utcnow)


class MarketDataPointModel(Base):
    """Individual price observations."""
    __tablename__ = "market_data_points"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    market_price_id: Mapped[int] = mapped_column(Integer, ForeignKey("market_prices.id", ondelete="CASCADE"), index=True)

    price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    currency: Mapped[Optional[str]] = mapped_column(String(3), default="USD")
    price_usd: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    source_type: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)

    grade: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    grade_numeric: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    condition_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    auction_house: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sale_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    lot_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    lot_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    dealer_name: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    confidence: Mapped[Optional[str]] = mapped_column(String(20), default="medium")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    market_price: Mapped["MarketPriceModel"] = relationship("MarketPriceModel", backref="data_points")


class CoinValuationModel(Base):
    """Valuation snapshots per coin."""
    __tablename__ = "coin_valuations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    coin_id: Mapped[int] = mapped_column(Integer, ForeignKey("coins_v2.id", ondelete="CASCADE"), index=True)

    valuation_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    purchase_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    purchase_currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    purchase_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    current_market_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    value_currency: Mapped[Optional[str]] = mapped_column(String(3), default="USD")
    market_confidence: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    comparable_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    comparable_avg_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    comparable_date_range: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    price_trend_6mo: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    price_trend_12mo: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    price_trend_36mo: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)

    gain_loss_usd: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    gain_loss_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)

    valuation_method: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    coin: Mapped["CoinModel"] = relationship("CoinModel", backref="valuations")


class WishlistItemModel(Base):
    """Acquisition targets."""
    __tablename__ = "wishlist_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    issuer: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    issuer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("vocab_terms.id"), nullable=True)
    mint: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    mint_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("vocab_terms.id"), nullable=True)
    year_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    year_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    denomination: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    metal: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    catalog_ref: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)
    catalog_ref_pattern: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    min_grade: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    min_grade_numeric: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    condition_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    max_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    target_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(3), default="USD")

    priority: Mapped[Optional[int]] = mapped_column(Integer, default=2, index=True)
    tags: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    series_slot_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("series_slots.id"), nullable=True)

    status: Mapped[Optional[str]] = mapped_column(String(20), default="wanted", index=True)
    acquired_coin_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("coins_v2.id"), nullable=True)
    acquired_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    acquired_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)

    notify_on_match: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    notify_email: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, onupdate=datetime.utcnow)


class PriceAlertModel(Base):
    """User alert configurations."""
    __tablename__ = "price_alerts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    attribution_key: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    coin_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("coins_v2.id", ondelete="SET NULL"), nullable=True, index=True)
    wishlist_item_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("wishlist_items.id", ondelete="CASCADE"), nullable=True, index=True)

    trigger_type: Mapped[str] = mapped_column(String(30), nullable=False)
    threshold_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    threshold_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    threshold_grade: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    status: Mapped[Optional[str]] = mapped_column(String(20), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    notification_sent: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    notification_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    notification_channel: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    cooldown_hours: Mapped[Optional[int]] = mapped_column(Integer, default=24)
    last_triggered_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


class WishlistMatchModel(Base):
    """Matched auction lots for wishlists."""
    __tablename__ = "wishlist_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    wishlist_item_id: Mapped[int] = mapped_column(Integer, ForeignKey("wishlist_items.id", ondelete="CASCADE"), index=True)

    match_type: Mapped[str] = mapped_column(String(30), nullable=False)
    match_source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    match_id: Mapped[str] = mapped_column(String(100), nullable=False)
    match_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    title: Mapped[str] = mapped_column(String(300), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    grade: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    grade_numeric: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    condition_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    estimate_low: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    estimate_high: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(3), default="USD")
    current_bid: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)

    auction_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    end_time: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    match_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), nullable=True)
    match_confidence: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    match_reasons: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    is_below_budget: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    is_below_market: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    value_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), nullable=True)

    notified: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    notified_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    dismissed: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, index=True)
    dismissed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    saved: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    wishlist_item: Mapped["WishlistItemModel"] = relationship("WishlistItemModel", backref="matches")


# =============================================================================
# Schema V3 - Phase 6: Collections & Sub-collections
# =============================================================================

class CollectionModel(Base):
    """Collection definitions with support for custom and smart collections."""
    __tablename__ = "collections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    slug: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    collection_type: Mapped[Optional[str]] = mapped_column(String(20), default="custom", index=True)
    smart_filter: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    series_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("series.id", ondelete="SET NULL"), nullable=True, index=True)

    cover_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    display_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    default_sort: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    default_view: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    coin_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    total_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    stats_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    is_favorite: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, index=True)
    is_hidden: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    is_public: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("collections.id", ondelete="SET NULL"), nullable=True, index=True)
    level: Mapped[Optional[int]] = mapped_column(Integer, default=0)

    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, onupdate=datetime.utcnow)

    parent: Mapped[Optional["CollectionModel"]] = relationship("CollectionModel", remote_side=[id], backref="children")


class CollectionCoinModel(Base):
    """Many-to-many linking for collections."""
    __tablename__ = "collection_coins"

    collection_id: Mapped[int] = mapped_column(Integer, ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True, index=True)
    coin_id: Mapped[int] = mapped_column(Integer, ForeignKey("coins_v2.id", ondelete="CASCADE"), primary_key=True, index=True)

    added_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, index=True)
    added_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    custom_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_featured: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    is_cover_coin: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    series_slot_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("series_slots.id", ondelete="SET NULL"), nullable=True)

    collection: Mapped["CollectionModel"] = relationship("CollectionModel", backref="coin_memberships")
    coin: Mapped["CoinModel"] = relationship("CoinModel", backref="collection_memberships")