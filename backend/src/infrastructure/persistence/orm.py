from typing import Optional, List
from decimal import Decimal
from datetime import date, datetime, timezone
from sqlalchemy import Integer, String, Text, Numeric, Date, DateTime, Boolean, ForeignKey, Table, Column, CheckConstraint, UniqueConstraint, Index
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


class CountermarkModel(Base):
    """
    ORM model for countermarks table (Phase 1.5b).

    Supports multiple countermarks per coin with full tracking of type,
    placement, condition, and attribution.
    """
    __tablename__ = "countermarks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    coin_id: Mapped[int] = mapped_column(Integer, ForeignKey("coins_v2.id", ondelete="CASCADE"), nullable=False, index=True)

    # Core fields (match existing database schema)
    countermark_type: Mapped[str] = mapped_column(String(15), nullable=False, server_default="uncertain")
    description: Mapped[str] = mapped_column(String(100), nullable=False, server_default="")
    placement: Mapped[str] = mapped_column(String(7), nullable=False, server_default="obverse")  # Legacy column

    # Optional/extended fields
    expanded: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Legacy column
    position: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    condition: Mapped[Optional[str]] = mapped_column(String(9), nullable=True)
    punch_shape: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # rectangular, circular, etc.
    authority: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    date_applied: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # Legacy column
    image_side: Mapped[Optional[str]] = mapped_column(String(7), nullable=True)  # Legacy column
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # Howgego number

    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationship back to coin
    coin: Mapped["CoinModel"] = relationship("CoinModel", back_populates="countermarks")

    __table_args__ = (
        Index("ix_countermarks_coin_type", "coin_id", "countermark_type"),
    )


class CoinModel(Base):
    __tablename__ = "coins_v2"

    # Check constraints and composite indexes for performance
    __table_args__ = (
        CheckConstraint('die_axis >= 0 AND die_axis <= 12', name='check_die_axis_range'),
        CheckConstraint('ngc_strike_grade IS NULL OR (ngc_strike_grade >= 1 AND ngc_strike_grade <= 5)', name='check_ngc_strike_grade_range'),
        CheckConstraint('ngc_surface_grade IS NULL OR (ngc_surface_grade >= 1 AND ngc_surface_grade <= 5)', name='check_ngc_surface_grade_range'),
        # Composite indexes for common filter patterns (30-50% faster filtered queries)
        Index('ix_coins_v2_category_metal', 'category', 'metal'),
        Index('ix_coins_v2_category_grading_state', 'category', 'grading_state'),
        Index('ix_coins_v2_issuer_year', 'issuer_id', 'year_start'),
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

    # -------------------------------------------------------------------------
    # Phase 1.5b: Strike Quality Detail & NGC Grade Components
    # -------------------------------------------------------------------------

    # Strike quality detail (5 columns)
    strike_quality_detail: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    is_double_struck: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    is_brockage: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    is_off_center: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    off_center_pct: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # 5-95%

    # NGC-specific Strike/Surface grades (3 columns)
    # NGC uses 1-5 scale for ancients; PCGS doesn't use this system
    ngc_strike_grade: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    ngc_surface_grade: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    is_fine_style: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    # Relationships
    images: Mapped[List["CoinImageModel"]] = relationship(back_populates="coin", cascade="all, delete-orphan")
    # UPDATED: Added cascade to prevent orphaned auction data
    auction_data: Mapped[Optional["AuctionDataModel"]] = relationship(back_populates="coin", uselist=False, cascade="all, delete-orphan")
    references: Mapped[List["CoinReferenceModel"]] = relationship(back_populates="coin", cascade="all, delete-orphan")
    provenance_events: Mapped[List["ProvenanceEventModel"]] = relationship(back_populates="coin", cascade="all, delete-orphan")
    monograms: Mapped[List["MonogramModel"]] = relationship(secondary=coin_monograms, back_populates="coins")
    # Phase 1.5b: Countermarks relationship
    countermarks: Mapped[List["CountermarkModel"]] = relationship(
        "CountermarkModel",
        back_populates="coin",
        cascade="all, delete-orphan",
        lazy="selectin"  # Prevent N+1
    )
    
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

    # Phase 3 enhancements
    sng_volume: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # SNG Copenhagen, von Aulock
    number_numeric: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)  # Parsed for range queries
    publication_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    rarity_code: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # R1-R5 from catalog
    full_citation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Full bibliographic citation
    plate_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Plate reference

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

    # Phase 3 enhancements
    attribution_confidence: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # certain, probable, possible, tentative
    catalog_rarity_note: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # "R2", "Very Rare"
    disagreement_note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Attribution disputes
    page_reference: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # "p. 234, pl. XV.7"
    variant_note: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)  # "var. b with AVGVSTI"

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
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, onupdate=lambda: datetime.now(timezone.utc))

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
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))


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
    recorded_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
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
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    # Variety Rarity Tracking (Phase 3)
    variety_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    die_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("dies.id", ondelete="SET NULL"), nullable=True, index=True)
    die_rarity_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    condition_rarity_threshold: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    rarity_context: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)

    coin: Mapped["CoinModel"] = relationship("CoinModel", backref="rarity_assessments")
    die: Mapped[Optional["DieModel"]] = relationship("DieModel", backref="rarity_assessments")


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
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

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
    __table_args__ = (
        Index("ix_llm_enrichments_capability_input_hash", "capability", "input_hash"),
        Index("ix_llm_enrichments_coin_capability", "coin_id", "capability"),
        Index("ix_llm_enrichments_coin_review_status", "coin_id", "review_status"),
    )

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

    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
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
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
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
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

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
    category: Mapped[Optional[str]] = mapped_column(String(30), nullable=True, index=True)
    catalog_ref: Mapped[Optional[str]] = mapped_column(String(100), nullable=True, index=True)

    avg_price_vf: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    avg_price_ef: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    avg_price_au: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    avg_price_ms: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    min_price_seen: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    max_price_seen: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    median_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)

    data_point_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    last_sale_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    last_updated: Mapped[Optional[datetime]] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))


class MarketDataPointModel(Base):
    """Individual price observations."""
    __tablename__ = "market_data_points"
    __table_args__ = (
        Index("ix_market_data_points_price_date", "market_price_id", "date"),
    )

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

    # Price breakdown for auction sales
    is_hammer_price: Mapped[Optional[bool]] = mapped_column(Boolean, default=True)
    buyers_premium_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)

    # Slabbed coin information
    is_slabbed: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    grading_service: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    certification_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    confidence: Mapped[Optional[str]] = mapped_column(String(20), default="medium")
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

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
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

    coin: Mapped["CoinModel"] = relationship("CoinModel", backref="valuations")


class WishlistItemModel(Base):
    """Acquisition targets."""
    __tablename__ = "wishlist_items"
    __table_args__ = (
        Index("ix_wishlist_items_status_priority", "status", "priority"),
    )

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
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, onupdate=lambda: datetime.now(timezone.utc))


class PriceAlertModel(Base):
    """User alert configurations."""
    __tablename__ = "price_alerts"
    __table_args__ = (
        Index("ix_price_alerts_status_trigger_type", "status", "trigger_type"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    attribution_key: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    coin_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("coins_v2.id", ondelete="SET NULL"), nullable=True, index=True)
    wishlist_item_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("wishlist_items.id", ondelete="CASCADE"), nullable=True, index=True)

    trigger_type: Mapped[str] = mapped_column(String(30), nullable=False)
    threshold_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(12, 2), nullable=True)
    threshold_pct: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    threshold_grade: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    status: Mapped[Optional[str]] = mapped_column(String(20), default="active", index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
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
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))

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
    purpose: Mapped[Optional[str]] = mapped_column(String(30), default="general", index=True)
    # purpose values: study, display, type_set, duplicates, reserves, insurance, general

    smart_filter: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    series_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("series.id", ondelete="SET NULL"), nullable=True, index=True)

    # Type set tracking
    is_type_set: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    type_set_definition: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    completion_percentage: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)

    # Display settings
    cover_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    cover_coin_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("coins_v2.id", ondelete="SET NULL"), nullable=True)
    color: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    icon: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    display_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    default_sort: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    default_view: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Cached statistics
    coin_count: Mapped[Optional[int]] = mapped_column(Integer, default=0)
    total_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2), nullable=True)
    stats_updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Flags
    is_favorite: Mapped[Optional[bool]] = mapped_column(Boolean, default=False, index=True)
    is_hidden: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    is_public: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    # Hierarchy (limited to 3 levels per numismatic review)
    parent_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("collections.id", ondelete="SET NULL"), nullable=True, index=True)
    level: Mapped[Optional[int]] = mapped_column(Integer, default=0)

    # Physical storage mapping (bridges digital to physical)
    storage_location: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)

    # Metadata
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True, onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    parent: Mapped[Optional["CollectionModel"]] = relationship("CollectionModel", remote_side=[id], backref="children")
    cover_coin: Mapped[Optional["CoinModel"]] = relationship("CoinModel", foreign_keys=[cover_coin_id])


class CollectionCoinModel(Base):
    """Many-to-many linking for collections with per-collection coin context."""
    __tablename__ = "collection_coins"

    collection_id: Mapped[int] = mapped_column(Integer, ForeignKey("collections.id", ondelete="CASCADE"), primary_key=True, index=True)
    coin_id: Mapped[int] = mapped_column(Integer, ForeignKey("coins_v2.id", ondelete="CASCADE"), primary_key=True, index=True)

    # Membership metadata
    added_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=lambda: datetime.now(timezone.utc), index=True)
    added_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)

    # Ordering
    position: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    custom_order: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Per-collection context notes
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Feature flags
    is_featured: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    is_cover_coin: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)

    # From numismatic review: placeholder and stats exclusion
    is_placeholder: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    # Temporary coin until upgrade found
    exclude_from_stats: Mapped[Optional[bool]] = mapped_column(Boolean, default=False)
    # Don't count in collection totals (duplicates, study pieces)

    # Type set tracking
    fulfills_type: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    # Which type requirement this coin satisfies
    series_slot_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("series_slots.id", ondelete="SET NULL"), nullable=True)

    # Relationships
    collection: Mapped["CollectionModel"] = relationship("CollectionModel", backref="coin_memberships")
    coin: Mapped["CoinModel"] = relationship("CoinModel", backref="collection_memberships")


# --- Phase 1.5d: Die Study Module ORM Models ---

class DieModel(Base):
    """ORM model for dies table - master die catalog."""
    __tablename__ = "dies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    die_identifier: Mapped[str] = mapped_column(String(100), nullable=False, unique=True, index=True)
    die_side: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    die_state: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    has_die_crack: Mapped[bool] = mapped_column(Boolean, server_default='0')
    has_die_clash: Mapped[bool] = mapped_column(Boolean, server_default='0')
    die_rotation_angle: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    reference_system: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reference_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    die_links: Mapped[List["DieLinkModel"]] = relationship(
        "DieLinkModel",
        back_populates="die",
        cascade="all, delete-orphan"
    )
    die_varieties: Mapped[List["DieVarietyModel"]] = relationship(
        "DieVarietyModel",
        back_populates="die",
        cascade="all, delete-orphan"
    )


class DieLinkModel(Base):
    """ORM model for die_links table - coins sharing same die."""
    __tablename__ = "die_links"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    die_id: Mapped[int] = mapped_column(Integer, ForeignKey("dies.id", ondelete="CASCADE"), nullable=False, index=True)
    coin_a_id: Mapped[int] = mapped_column(Integer, ForeignKey("coins_v2.id", ondelete="CASCADE"), nullable=False)
    coin_b_id: Mapped[int] = mapped_column(Integer, ForeignKey("coins_v2.id", ondelete="CASCADE"), nullable=False)
    confidence: Mapped[str] = mapped_column(String(20), nullable=False)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        CheckConstraint('coin_a_id < coin_b_id', name='check_coin_order'),
        UniqueConstraint('die_id', 'coin_a_id', 'coin_b_id', name='uq_die_link'),
        Index('ix_die_links_coin_a', 'coin_a_id', 'die_id'),
        Index('ix_die_links_coin_b', 'coin_b_id', 'die_id'),
    )

    # Relationships
    die: Mapped["DieModel"] = relationship("DieModel", back_populates="die_links")
    coin_a: Mapped["CoinModel"] = relationship("CoinModel", foreign_keys=[coin_a_id])
    coin_b: Mapped["CoinModel"] = relationship("CoinModel", foreign_keys=[coin_b_id])


class DiePairingModel(Base):
    """ORM model for die_pairings table - obverse-reverse die combinations."""
    __tablename__ = "die_pairings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    obverse_die_id: Mapped[int] = mapped_column(Integer, ForeignKey("dies.id", ondelete="CASCADE"), nullable=False, index=True)
    reverse_die_id: Mapped[int] = mapped_column(Integer, ForeignKey("dies.id", ondelete="CASCADE"), nullable=False, index=True)
    reference_system: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reference_number: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    rarity_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    specimen_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint('obverse_die_id', 'reverse_die_id', name='uq_die_pairing'),
    )

    # Relationships
    obverse_die: Mapped["DieModel"] = relationship("DieModel", foreign_keys=[obverse_die_id])
    reverse_die: Mapped["DieModel"] = relationship("DieModel", foreign_keys=[reverse_die_id])


class DieVarietyModel(Base):
    """ORM model for die_varieties table - die variety classifications."""
    __tablename__ = "die_varieties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    coin_id: Mapped[int] = mapped_column(Integer, ForeignKey("coins_v2.id", ondelete="CASCADE"), nullable=False, index=True)
    die_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("dies.id", ondelete="SET NULL"), nullable=True, index=True)
    variety_code: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    variety_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    distinguishing_features: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    coin: Mapped["CoinModel"] = relationship("CoinModel", backref="die_varieties")
    die: Mapped[Optional["DieModel"]] = relationship("DieModel", back_populates="die_varieties")


# --- Phase 2: Attribution Confidence ORM Models ---

class AttributionHypothesisModel(Base):
    """ORM model for attribution_hypotheses table - multi-hypothesis attributions with field-level confidence."""
    __tablename__ = "attribution_hypotheses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    coin_id: Mapped[int] = mapped_column(Integer, ForeignKey("coins_v2.id", ondelete="CASCADE"), nullable=False, index=True)
    hypothesis_rank: Mapped[int] = mapped_column(Integer, nullable=False)

    # Field-level attribution with confidence
    issuer: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    issuer_confidence: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    mint: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    mint_confidence: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    year_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    year_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    date_confidence: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    denomination: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    denomination_confidence: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    # Overall confidence
    overall_certainty: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    confidence_score: Mapped[Optional[Decimal]] = mapped_column(Numeric(3, 2), nullable=True)

    # Evidence
    attribution_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_support: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    source: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        UniqueConstraint('coin_id', 'hypothesis_rank', name='uq_attribution_hypothesis_rank'),
        Index('ix_attribution_hypotheses_coin_rank', 'coin_id', 'hypothesis_rank'),
    )

    # Relationships
    coin: Mapped["CoinModel"] = relationship("CoinModel", backref="attribution_hypotheses")