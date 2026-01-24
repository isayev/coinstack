"""Coin model - Clean refactor with enhanced enums and fields."""
from sqlalchemy import (
    Column, Integer, String, Numeric, Date, Boolean,
    ForeignKey, Enum, Text, JSON, DateTime, CheckConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum
from app.database import Base


class Category(enum.Enum):
    """Coin category - ordered chronologically."""
    GREEK = "greek"
    CELTIC = "celtic"
    REPUBLIC = "republic"
    IMPERIAL = "imperial"
    PROVINCIAL = "provincial"
    JUDAEAN = "judaean"
    BYZANTINE = "byzantine"
    MIGRATION = "migration"          # Ostrogothic, Vandal, etc.
    PSEUDO_ROMAN = "pseudo_roman"    # Imitations
    OTHER = "other"


class Metal(enum.Enum):
    """Coin metal type - ordered by value/rarity."""
    GOLD = "gold"
    ELECTRUM = "electrum"        # Gold-silver alloy (Greek)
    SILVER = "silver"
    BILLON = "billon"
    POTIN = "potin"              # Tin-rich bronze (Celtic/Alexandrian)
    ORICHALCUM = "orichalcum"
    BRONZE = "bronze"
    COPPER = "copper"
    LEAD = "lead"                # Tesserae/tokens
    AE = "ae"                    # Generic bronze when composition unknown
    UNCERTAIN = "uncertain"      # When metal cannot be determined


class DatingCertainty(enum.Enum):
    """Dating certainty level."""
    EXACT = "exact"
    NARROW = "narrow"
    BROAD = "broad"
    UNKNOWN = "unknown"


class GradeService(enum.Enum):
    """Grading service."""
    NGC = "ngc"
    PCGS = "pcgs"
    SELF = "self"
    DEALER = "dealer"


class HolderType(enum.Enum):
    """Holder type."""
    NGC_SLAB = "ngc_slab"
    PCGS_SLAB = "pcgs_slab"
    FLIP = "flip"
    CAPSULE = "capsule"
    TRAY = "tray"
    RAW = "raw"


class Rarity(enum.Enum):
    """Rarity level."""
    COMMON = "common"
    SCARCE = "scarce"
    RARE = "rare"
    VERY_RARE = "very_rare"
    EXTREMELY_RARE = "extremely_rare"
    UNIQUE = "unique"


class Orientation(enum.Enum):
    """Coin orientation for photography/display."""
    OBVERSE_UP = "obverse_up"
    REVERSE_UP = "reverse_up"
    ROTATED = "rotated"


class Coin(Base):
    """Coin model - Enhanced with die study, precision, and constraints."""
    
    __tablename__ = "coins"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Classification
    category = Column(Enum(Category), nullable=False, index=True)
    sub_category = Column(String(50), index=True)  # "Julio-Claudian", "Flavian", etc.
    denomination = Column(String(50), nullable=False, index=True)
    metal = Column(Enum(Metal), nullable=False, index=True)
    series = Column(String(100))
    
    # People
    issuing_authority = Column(String(100), nullable=False, index=True)
    portrait_subject = Column(String(100), index=True)
    status = Column(String(50))
    
    # Chronology
    reign_start = Column(Integer)
    reign_end = Column(Integer)
    mint_year_start = Column(Integer)
    mint_year_end = Column(Integer)
    is_circa = Column(Boolean, default=False)  # Date uncertainty flag
    dating_certainty = Column(Enum(DatingCertainty), default=DatingCertainty.BROAD)
    dating_notes = Column(String(255))
    
    # Physical Attributes - Enhanced precision
    weight_g = Column(Numeric(6, 3))  # 0.001g precision for die studies
    diameter_mm = Column(Numeric(5, 2))
    diameter_min_mm = Column(Numeric(5, 2))
    thickness_mm = Column(Numeric(4, 2))
    die_axis = Column(Integer)  # 0-12 clock position, validated by constraint
    orientation = Column(Enum(Orientation), default=Orientation.OBVERSE_UP)
    is_test_cut = Column(Boolean, default=False)  # Provincial diagnostic cut
    
    # Design: Obverse
    obverse_legend = Column(String(255))
    obverse_legend_expanded = Column(Text)
    obverse_description = Column(Text)
    obverse_symbols = Column(String(255))
    
    # Design: Reverse
    reverse_legend = Column(String(255))
    reverse_legend_expanded = Column(Text)
    reverse_description = Column(Text)
    reverse_symbols = Column(String(255))
    exergue = Column(String(100))
    
    # Mint
    mint_id = Column(Integer, ForeignKey("mints.id"))
    mint = relationship("Mint", back_populates="coins")
    officina = Column(String(20))
    script = Column(String(20))
    
    # Grading
    grade_service = Column(Enum(GradeService))
    grade = Column(String(50))
    strike_quality = Column(Integer)
    surface_quality = Column(Integer)
    certification_number = Column(String(50))
    surface_issues = Column(JSON)
    eye_appeal = Column(String(50))
    toning_description = Column(String(255))
    style_notes = Column(String(255))
    
    # Acquisition
    acquisition_date = Column(Date)
    acquisition_price = Column(Numeric(10, 2))
    acquisition_currency = Column(String(3), default="USD")
    acquisition_source = Column(String(100))
    acquisition_url = Column(String(500))
    
    # Valuation
    estimate_low = Column(Numeric(10, 2))
    estimate_high = Column(Numeric(10, 2))
    estimate_date = Column(Date)
    estimated_value_usd = Column(Numeric(10, 2))  # From comps
    insured_value = Column(Numeric(10, 2))
    
    # Storage
    holder_type = Column(Enum(HolderType))
    storage_location = Column(String(50))
    for_sale = Column(Boolean, default=False)
    asking_price = Column(Numeric(10, 2))
    
    # Research
    rarity = Column(Enum(Rarity))
    rarity_notes = Column(String(255))
    historical_significance = Column(Text)
    die_match_notes = Column(Text)
    personal_notes = Column(Text)
    provenance_notes = Column(Text)
    
    # Die Study Linkage - Self-referential for die matches
    die_study_obverse_id = Column(Integer, ForeignKey("coins.id"), nullable=True)
    die_study_reverse_id = Column(Integer, ForeignKey("coins.id"), nullable=True)
    die_study_group = Column(String(50))
    
    # LLM Enrichment
    llm_enriched = Column(JSON)
    llm_enriched_at = Column(DateTime)
    
    # Constraints
    __table_args__ = (
        CheckConstraint(
            'die_axis IS NULL OR (die_axis >= 0 AND die_axis <= 12)',
            name='ck_die_axis_range'
        ),
    )
    
    # Relationships
    references = relationship("CoinReference", back_populates="coin", cascade="all, delete-orphan")
    provenance_events = relationship(
        "ProvenanceEvent", back_populates="coin", cascade="all, delete-orphan",
        order_by="ProvenanceEvent.sort_order"
    )
    images = relationship("CoinImage", back_populates="coin", cascade="all, delete-orphan")
    tags = relationship("CoinTag", back_populates="coin", cascade="all, delete-orphan")
    countermarks = relationship("Countermark", back_populates="coin", cascade="all, delete-orphan")
    auction_data = relationship("AuctionData", back_populates="coin", cascade="all, delete-orphan")
    
    # Die study relationships
    obverse_die_matches = relationship(
        "Coin", 
        foreign_keys=[die_study_obverse_id],
        remote_side=[id],
        backref="obverse_die_source"
    )
    reverse_die_matches = relationship(
        "Coin",
        foreign_keys=[die_study_reverse_id],
        remote_side=[id],
        backref="reverse_die_source"
    )
