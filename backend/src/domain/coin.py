from dataclasses import dataclass, field
from typing import List, Dict, Any, Self
from datetime import date as DateType, datetime as DateTimeType
from decimal import Decimal
from enum import Enum

# --- Enums ---

class Metal(str, Enum):
    GOLD = "gold"
    SILVER = "silver"
    BRONZE = "bronze"
    COPPER = "copper"
    ELECTRUM = "electrum"
    BILLON = "billon"
    POTIN = "potin"
    ORICHALCUM = "orichalcum"
    LEAD = "lead"          # PB - ancient tokens, tesserae
    AE = "ae"              # Generic bronze/copper (standard numismatic abbreviation)

class Category(str, Enum):
    # Core categories
    GREEK = "greek"
    ROMAN_IMPERIAL = "roman_imperial"
    ROMAN_REPUBLIC = "roman_republic"
    ROMAN_PROVINCIAL = "roman_provincial"
    BYZANTINE = "byzantine"
    MEDIEVAL = "medieval"
    # Breakaway empires (historically distinct coinages)
    GALLIC_EMPIRE = "gallic_empire"        # 260-274 AD - Postumus, Victorinus, Tetrici
    PALMYRENE_EMPIRE = "palmyrene_empire"  # 270-273 AD - Zenobia, Vabalathus
    ROMANO_BRITISH = "romano_british"      # 286-296 AD - Carausius, Allectus
    # Other ancient categories
    CELTIC = "celtic"
    JUDAEAN = "judaean"
    PARTHIAN = "parthian"
    SASANIAN = "sasanian"
    MIGRATION = "migration"                 # Post-Roman 'barbarian' coinage
    OTHER = "other"

class GradingState(str, Enum):
    RAW = "raw"
    SLABBED = "slabbed"
    CAPSULE = "capsule"
    FLIP = "flip"

class GradeService(str, Enum):
    NGC = "ngc"
    PCGS = "pcgs"
    ICG = "icg"
    ANACS = "anacs"
    NONE = "none"

class IssueStatus(str, Enum):
    """Manufacturing status of the coin."""
    OFFICIAL = "official"
    FOURREE = "fourree"
    IMITATION = "imitation"
    BARBAROUS = "barbarous"
    MODERN_FAKE = "modern_fake"
    TOOLING_ALTERED = "tooling_altered"


# --- Phase 1: Schema V3 Enums ---

class AuthorityType(str, Enum):
    """Type of secondary authority (Greek magistrates, provincial governors)."""
    MAGISTRATE = "magistrate"
    SATRAP = "satrap"
    DYNAST = "dynast"
    STRATEGOS = "strategos"
    ARCHON = "archon"
    EPISTATES = "epistates"


class PortraitRelationship(str, Enum):
    """Relationship of portrait subject to issuing authority."""
    SELF = "self"
    CONSORT = "consort"
    HEIR = "heir"
    PARENT = "parent"
    PREDECESSOR = "predecessor"
    COMMEMORATIVE = "commemorative"
    DIVUS = "divus"
    DIVA = "diva"


class WeightStandard(str, Enum):
    """Ancient weight standards for coinage."""
    ATTIC = "attic"
    AEGINETAN = "aeginetan"
    CORINTHIAN = "corinthian"
    PHOENICIAN = "phoenician"
    DENARIUS_EARLY = "denarius_early"
    DENARIUS_REFORMED = "denarius_reformed"
    ANTONINIANUS = "antoninianus"


class FlanShape(str, Enum):
    """Shape of the coin flan."""
    ROUND = "round"
    IRREGULAR = "irregular"
    OVAL = "oval"
    SQUARE = "square"
    SCYPHATE = "scyphate"


class FlanType(str, Enum):
    """Manufacturing method of the flan."""
    CAST = "cast"
    STRUCK = "struck"
    CUT_FROM_BAR = "cut_from_bar"
    HAMMERED = "hammered"


class ToolingExtent(str, Enum):
    """Extent of tooling or repair on the coin."""
    NONE = "none"
    MINOR = "minor"
    MODERATE = "moderate"
    SIGNIFICANT = "significant"
    EXTENSIVE = "extensive"


class CenteringQuality(str, Enum):
    """Quality of strike centering."""
    WELL_CENTERED = "well-centered"
    SLIGHTLY_OFF = "slightly_off"
    OFF_CENTER = "off_center"
    SIGNIFICANTLY_OFF = "significantly_off"


class DieState(str, Enum):
    """State of the die used for striking."""
    FRESH = "fresh"
    EARLY = "early"
    MIDDLE = "middle"
    LATE = "late"
    WORN = "worn"
    BROKEN = "broken"
    REPAIRED = "repaired"


class ProvenanceEventType(str, Enum):
    """Types of provenance events in a coin's ownership history."""
    AUCTION = "auction"
    DEALER = "dealer"
    COLLECTION = "collection"
    PRIVATE_SALE = "private_sale"
    PUBLICATION = "publication"
    HOARD_FIND = "hoard_find"
    ESTATE = "estate"
    ACQUISITION = "acquisition"  # My purchase - final entry in pedigree
    UNKNOWN = "unknown"


class ProvenanceSource(str, Enum):
    """Origin/source of provenance data entry."""
    MANUAL_ENTRY = "manual_entry"
    SCRAPER = "scraper"
    IMPORT = "import"
    LLM_ENRICHMENT = "llm_enrichment"
    MIGRATION = "migration"
    AUTO_ACQUISITION = "auto_acquisition"  # Auto-created from acquisition data


# --- Phase 2: Schema V3 - Grading History & Rarity Enums ---

class GradingEventType(str, Enum):
    """Type of grading event in a coin's TPG lifecycle."""
    INITIAL = "initial"          # First submission to TPG
    CROSSOVER = "crossover"      # Moving from one TPG service to another
    REGRADE = "regrade"          # Resubmission to same service for new grade
    CRACK_OUT = "crack_out"      # Removed from slab (returned to raw)


class RaritySystem(str, Enum):
    """Rarity rating systems used in numismatics."""
    RIC = "ric"                          # RIC rarity codes (C, S, R1-R5, RR, RRR)
    CATALOG = "catalog"                  # Generic catalog rating
    CENSUS = "census"                    # TPG population-based
    MARKET_FREQUENCY = "market_frequency"  # Auction appearance analysis


class RaritySourceType(str, Enum):
    """Origin/source of rarity assessment data."""
    CATALOG = "catalog"                  # Published catalog (RIC, Sear, etc.)
    CENSUS_DATA = "census_data"          # NGC/PCGS population data
    AUCTION_ANALYSIS = "auction_analysis"  # Market appearance tracking
    EXPERT_OPINION = "expert_opinion"    # Dealer/expert assessment


class RarityConfidence(str, Enum):
    """Confidence level for a rarity assessment."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"

# --- Value Objects ---

@dataclass(frozen=True, slots=True)
class Dimensions:
    diameter_mm: Decimal
    weight_g: Decimal | None = None  # Optional e.g. slabbed coins where weight cannot be measured
    die_axis: int | None = None
    specific_gravity: Decimal | None = None

    def __post_init__(self):
        if self.weight_g is not None and self.weight_g < 0:
            raise ValueError("Weight must be positive")
        if self.diameter_mm < 0:
            raise ValueError("Diameter must be positive")
        if self.die_axis is not None and not (0 <= self.die_axis <= 12):
            raise ValueError("Die axis must be between 0 and 12")

@dataclass(frozen=True, slots=True)
class Attribution:
    issuer: str
    issuer_id: int | None = None
    mint: str | None = None
    mint_id: int | None = None
    year_start: int | None = None
    year_end: int | None = None

@dataclass(frozen=True, slots=True)
class GradingDetails:
    grading_state: GradingState
    grade: str
    service: GradeService | None = None
    certification_number: str | None = None
    strike: str | None = None
    surface: str | None = None

    def __post_init__(self):
        if self.grading_state == GradingState.SLABBED and not self.service:
            raise ValueError("Slabbed coins must have a grading service specified")

@dataclass(frozen=True, slots=True)
class AcquisitionDetails:
    price: Decimal
    currency: str
    source: str
    date: DateType | None = None
    url: str | None = None

    def __post_init__(self):
        if self.price < 0:
            raise ValueError("Price cannot be negative")

@dataclass(frozen=True, slots=True)
class Design:
    """Coin design details - legends, descriptions, and exergue text."""
    obverse_legend: str | None = None       # "IMP CAES DOMIT AVG GERM COS XVI..."
    obverse_description: str | None = None  # "laureate head of Domitian right"
    reverse_legend: str | None = None       # "MONETA AVGVSTI"
    reverse_description: str | None = None  # "Moneta standing left, holding scales"
    exergue: str | None = None              # Text below main reverse design

@dataclass(frozen=True, slots=True)
class CatalogReference:
    """A single catalog reference for a coin."""
    catalog: str              # "RIC", "Crawford", "Sear", "RSC", "RPC", "BMC", "SNG"
    number: str               # "756", "44/5", "1234a" (may include variant e.g. 351b)
    volume: str | None = None   # "II", "V.1", etc. (Roman for RIC/RPC)
    suffix: str | None = None   # Additional qualifiers
    raw_text: str = ""        # Original text as found
    is_primary: bool = False  # Primary reference for this coin
    notes: str | None = None  # Additional notes about this reference
    source: str | None = None   # "user" | "import" | "scraper" | "llm_approved" | "catalog_lookup"
    # Optional catalog-specific fields (backward compatible)
    variant: str | None = None   # e.g. "a", "b" (RIC, Crawford, DOC)
    mint: str | None = None     # RIC VI+ mint code, BMCRR/BMC Greek
    supplement: str | None = None  # RPC "S", "S2"
    collection: str | None = None  # SNG collection (e.g. "Copenhagen", "ANS")
    # Phase 3 enhancements
    attribution_confidence: str | None = None  # certain, probable, possible, tentative
    catalog_rarity_note: str | None = None  # "R2", "Very Rare" from catalog
    disagreement_note: str | None = None  # Attribution disputes
    page_reference: str | None = None  # "p. 234, pl. XV.7"
    variant_note: str | None = None  # "var. b with AVGVSTI"


@dataclass(frozen=True, slots=True)
class ReferenceConcordance:
    """
    Cross-reference linking between equivalent catalog references.

    Example: RIC 207 = RSC 112 = BMC 298 = Cohen 169
    All linked by the same concordance_group_id.
    """
    id: int | None = None
    concordance_group_id: str = ""  # UUID grouping equivalent refs
    reference_type_id: int = 0
    confidence: float = 1.0  # 1.0 = exact match, 0.5 = possible
    source: str | None = None  # ocre, crro, user, literature
    notes: str | None = None
    created_at: DateTimeType | None = None


@dataclass(frozen=True, slots=True)
class ExternalCatalogLink:
    """
    Link to an external online catalog database.

    Supports OCRE, Nomisma, CRRO, RPC Online, ACSearch, CoinProject.
    """
    id: int | None = None
    reference_type_id: int = 0
    catalog_source: str = ""  # ocre, nomisma, crro, rpc_online, acsearch
    external_id: str = ""  # e.g., "ric.3.ant.42" for OCRE
    external_url: str | None = None  # Direct URL to record
    external_data: str | None = None  # JSON metadata from source
    last_synced_at: DateTimeType | None = None
    sync_status: str = "pending"  # pending, synced, error, not_found


@dataclass(frozen=True, slots=True)
class ProvenanceEntry:
    """
    A single provenance event in a coin's ownership history.

    Supports flexible detail levels from minimal ("Ex Hunt Collection")
    to complete auction records with full financial data.

    The ACQUISITION event type represents the current owner's purchase,
    serving as the final entry in the pedigree timeline.
    """
    # Identity
    id: int | None = None

    # Event Classification
    event_type: ProvenanceEventType = ProvenanceEventType.UNKNOWN
    source_name: str = ""  # UNIFIED FIELD: auction house, dealer, collection name, etc.

    # Dating (flexible: exact date OR approximate string)
    event_date: DateType | None = None
    date_string: str | None = None  # "1920s", "before 1950", "circa 1840"

    # Auction Details (when applicable)
    sale_name: str | None = None  # "January 2024 NYINC Signature Sale"
    sale_number: str | None = None  # Auction catalog number
    lot_number: str | None = None
    catalog_reference: str | None = None  # "Heritage 3456:245"

    # Financial Data (optional)
    hammer_price: Decimal | None = None
    buyers_premium_pct: Decimal | None = None  # 20.0 for 20%
    total_price: Decimal | None = None
    currency: str | None = None  # ISO 4217 code (USD, EUR, GBP)

    # Documentation
    notes: str | None = None  # Free text, historical context
    url: str | None = None
    receipt_available: bool = False

    # Metadata
    source_origin: ProvenanceSource = ProvenanceSource.MANUAL_ENTRY
    auction_data_id: int | None = None  # Link to scraped auction data
    sort_order: int = 0  # Display order (0 = earliest, highest = most recent/acquisition)

    # Legacy/computed field for display
    raw_text: str = ""  # "Heritage Auctions, 2024, lot 3245"

    def __post_init__(self):
        """Validate provenance entry data."""
        if self.hammer_price is not None and self.hammer_price < 0:
            raise ValueError("Hammer price cannot be negative")
        if self.total_price is not None and self.total_price < 0:
            raise ValueError("Total price cannot be negative")
        if self.buyers_premium_pct is not None and not (Decimal(0) <= self.buyers_premium_pct <= Decimal(100)):
            raise ValueError("Buyer's premium must be between 0 and 100%")

    def compute_total_price(self) -> Decimal | None:
        """Calculate total price from hammer + premium if not explicitly set."""
        if self.total_price is not None:
            return self.total_price
        if self.hammer_price is not None and self.buyers_premium_pct is not None:
            premium = self.hammer_price * (self.buyers_premium_pct / Decimal(100))
            return self.hammer_price + premium
        return self.hammer_price  # Return hammer if no premium

    def build_raw_text(self) -> str:
        """Generate display string from components."""
        parts = []
        if self.source_name:
            parts.append(self.source_name)
        if self.event_date:
            parts.append(str(self.event_date.year))
        elif self.date_string:
            parts.append(self.date_string)
        if self.sale_name:
            parts.append(self.sale_name)
        if self.lot_number:
            parts.append(f"lot {self.lot_number}")
        return ", ".join(parts) if parts else ""

    @property
    def is_acquisition(self) -> bool:
        """Check if this is the current owner's acquisition entry."""
        return self.event_type == ProvenanceEventType.ACQUISITION

    @property
    def display_year(self) -> int | None:
        """Extract year for timeline sorting."""
        if self.event_date:
            return self.event_date.year
        if self.date_string:
            # Try to extract year from date_string like "1920s", "1985", "circa 1840"
            import re
            match = re.search(r'\b(1[0-9]{3}|20[0-2][0-9])\b', self.date_string)
            if match:
                return int(match.group(1))
        return None

@dataclass(frozen=True, slots=True)
class CoinImage:
    """Represents an image of the coin."""
    url: str
    image_type: str # 'obverse', 'reverse', 'slab', etc.
    is_primary: bool = False

@dataclass(frozen=True, slots=True)
class Monogram:
    """Represents a Monogram linked to a coin."""
    id: int | None
    label: str
    image_url: str | None = None
    vector_data: str | None = None

@dataclass(frozen=True, slots=True)
class DieInfo:
    """Research-grade die study information."""
    obverse_die_id: str | None = None
    reverse_die_id: str | None = None

@dataclass(frozen=True, slots=True)
class FindData:
    """Archaeological context or find data."""
    find_spot: str | None = None
    find_date: DateType | None = None


# --- Phase 1: Schema V3 Value Objects ---

@dataclass(frozen=True, slots=True)
class SecondaryAuthority:
    """Secondary authority information (Greek magistrates, provincial governors)."""
    name: str | None = None
    term_id: int | None = None
    authority_type: str | None = None  # magistrate, satrap, dynast, etc.


@dataclass(frozen=True, slots=True)
class CoRuler:
    """Co-ruler information for joint reigns (Byzantine, Imperial)."""
    name: str | None = None
    term_id: int | None = None
    portrait_relationship: str | None = None  # self, consort, heir, etc.


@dataclass(frozen=True, slots=True)
class PhysicalEnhancements:
    """Enhanced physical characteristics from Phase 1."""
    weight_standard: str | None = None  # attic, aeginetan, etc.
    expected_weight_g: Decimal | None = None
    flan_shape: str | None = None  # round, irregular, oval, etc.
    flan_type: str | None = None  # cast, struck, hammered, etc.
    flan_notes: str | None = None


@dataclass(frozen=True, slots=True)
class SecondaryTreatments:
    """Secondary treatments and modifications to the coin."""
    # Overstrikes
    is_overstrike: bool = False
    undertype_visible: str | None = None
    undertype_attribution: str | None = None
    # Test cuts
    has_test_cut: bool = False
    test_cut_count: int | None = None
    test_cut_positions: str | None = None
    # Other marks
    has_bankers_marks: bool = False
    has_graffiti: bool = False
    graffiti_description: str | None = None
    # Mounting evidence
    was_mounted: bool = False
    mount_evidence: str | None = None


@dataclass(frozen=True, slots=True)
class ToolingRepairs:
    """Tooling and repair information."""
    tooling_extent: str | None = None  # none, minor, moderate, significant, extensive
    tooling_details: str | None = None
    has_ancient_repair: bool = False
    ancient_repairs: str | None = None


@dataclass(frozen=True, slots=True)
class Centering:
    """Strike centering information."""
    centering: str | None = None  # well-centered, slightly_off, off_center, significantly_off
    centering_notes: str | None = None


@dataclass(frozen=True, slots=True)
class DieStudyEnhancements:
    """Enhanced die study information with separate states per side."""
    obverse_die_state: str | None = None  # fresh, early, middle, late, worn, broken, repaired
    reverse_die_state: str | None = None
    die_break_description: str | None = None


@dataclass(frozen=True, slots=True)
class GradingTPGEnhancements:
    """TPG grading enhancements (NGC/PCGS features)."""
    grade_numeric: int | None = None  # 50, 53, 55, 58, 60, 62-70
    grade_designation: str | None = None  # Fine Style, Choice, Gem, Superb Gem
    has_star_designation: bool = False
    photo_certificate: bool = False
    verification_url: str | None = None


@dataclass(frozen=True, slots=True)
class ChronologyEnhancements:
    """Enhanced chronological information."""
    date_period_notation: str | None = None  # "c. 150-100 BC", "late 3rd century AD"
    emission_phase: str | None = None  # First Issue, Second Issue, Reform Coinage, etc.


@dataclass(frozen=True, slots=True)
class EnrichmentData:
    """LLM-generated enrichment data and suggestions."""
    historical_significance: str | None = None
    enriched_at: str | None = None
    analysis_sections: str | None = None     # JSON-encoded analysis sections
    suggested_references: List[str] | None = None
    suggested_rarity: Dict[str, Any] | None = None
    suggested_design: Dict[str, Any] | None = None
    suggested_attribution: Dict[str, Any] | None = None


# --- Phase 2: Schema V3 - Grading History & Rarity Value Objects ---

@dataclass(frozen=True, slots=True)
class GradingHistoryEntry:
    """
    A single grading event in a coin's TPG lifecycle.

    Tracks the complete grading history from raw to slabbed, including
    crossovers, regrades, and crack-outs. Each entry represents a snapshot
    of the coin's grading state at a point in time.
    """
    # Identity
    id: int | None = None
    coin_id: int | None = None

    # Grading state at this point
    grading_state: str | None = None      # raw, slabbed, capsule, flip
    grade: str | None = None              # Ch XF, MS 63, etc.
    grade_service: str | None = None      # ngc, pcgs, icg, anacs
    certification_number: str | None = None
    strike_quality: str | None = None     # NGC/PCGS 1-5 scale
    surface_quality: str | None = None    # NGC/PCGS 1-5 scale
    grade_numeric: int | None = None      # 50, 53, 55, 58, 60, 62-70
    designation: str | None = None        # Fine Style, Choice, Gem, etc.
    has_star: bool = False                # NGC star designation
    photo_cert: bool = False              # Photo certificate
    verification_url: str | None = None   # NGC/PCGS verification URL

    # Event tracking
    event_type: str = "initial"           # initial, crossover, regrade, crack_out
    graded_date: DateType | None = None   # Date the grading occurred
    recorded_at: str | None = None        # When this record was created (ISO timestamp)
    submitter: str | None = None          # Who submitted for grading
    turnaround_days: int | None = None    # Days from submission to receipt
    grading_fee: Decimal | None = None    # Cost of grading service
    notes: str | None = None              # Additional notes

    # Ordering and status
    sequence_order: int = 0               # Order in timeline (0 = first)
    is_current: bool = False              # Is this the current grading state?


@dataclass(frozen=True, slots=True)
class RarityAssessment:
    """
    A rarity assessment from a specific source.

    Supports multiple rarity assessments per coin from different sources
    (catalog, census, market analysis) with grade-conditional support
    for TPG-specific population data.
    """
    # Identity
    id: int | None = None
    coin_id: int | None = None

    # Rarity rating
    rarity_code: str = ""                 # C, S, R1-R5, RR, RRR, UNIQUE
    rarity_system: str = "ric"            # ric, catalog, census, market_frequency
    source_type: str = "catalog"          # catalog, census_data, auction_analysis, expert_opinion
    source_name: str | None = None        # "RIC II.1", "NGC Census", etc.
    source_url: str | None = None         # URL to source if available
    source_date: DateType | None = None   # When data was retrieved/published

    # Grade-conditional rarity (for TPG census data)
    grade_range_low: str | None = None    # Applies to grades >= this
    grade_range_high: str | None = None   # Applies to grades <= this
    grade_conditional_notes: str | None = None  # "R3 in XF+, R5 in MS"

    # Census data (when source_type is census_data)
    census_total: int | None = None       # Total graded by service
    census_this_grade: int | None = None  # Graded at this specific grade
    census_finer: int | None = None       # Graded higher than this grade
    census_date: DateType | None = None   # When census was captured

    # Metadata
    confidence: str = "medium"            # high, medium, low
    notes: str | None = None              # Additional context
    is_primary: bool = False              # Primary rarity assessment
    created_at: str | None = None         # When this record was created (ISO timestamp)


@dataclass(slots=True)
class CensusSnapshot:
    """
    A point-in-time census population snapshot from NGC/PCGS.

    Tracks population data over time to enable trend analysis and
    track changes in certified populations for specific coin types.
    """
    # Identity
    id: int | None = None
    coin_id: int | None = None

    # Service and timing
    service: str = ""                     # ngc, pcgs
    snapshot_date: DateType | None = None # When census was captured

    # Population data
    total_graded: int = 0                 # Total graded by this service
    grade_breakdown: str | None = None    # JSON: {"VF": 10, "EF": 5, "AU": 2}
    coins_at_grade: int | None = None     # Population at this coin's specific grade
    coins_finer: int | None = None        # Population at finer grades
    percentile: Decimal | None = None     # Where this coin ranks (top X%)

    # Reference for lookup
    catalog_reference: str | None = None  # e.g., "RIC III 42" used for census lookup
    notes: str | None = None              # Additional context


# --- Phase 4: Schema V3 - LLM Architecture Enums ---

class LLMReviewStatus(str, Enum):
    """Review status for LLM enrichments.

    Status workflow:
    - PENDING: Awaiting human review (default for new enrichments)
    - PROVISIONAL: Auto-approved based on high confidence, may need spot-check
    - APPROVED: Explicitly approved by human reviewer
    - REJECTED: Rejected as incorrect or low quality
    - SUPERSEDED: Replaced by a newer enrichment version
    """
    PENDING = "pending"
    PROVISIONAL = "provisional"  # High-confidence auto-approval
    APPROVED = "approved"
    REJECTED = "rejected"
    SUPERSEDED = "superseded"


class LLMQualityFlags:
    """Standardized quality flags for LLM enrichments.

    These flags help identify potential issues that may require review.
    Multiple flags can be combined with comma separation.
    """
    UNCERTAIN = "uncertain"           # Model expressed uncertainty
    LOW_CONFIDENCE = "low_confidence"  # Confidence below threshold
    HALLUCINATION_RISK = "hallucination_risk"  # Potential hallucination detected
    NEEDS_CITATION = "needs_citation"  # Attribution requires source verification
    AMBIGUOUS_INPUT = "ambiguous_input"  # Input data was ambiguous
    PARTIAL_DATA = "partial_data"      # Some expected fields missing
    CONFLICTING_DATA = "conflicting_data"  # Input contained contradictions
    RARE_TYPE = "rare_type"           # Unusual coin type, extra verification needed


# Capability confidence thresholds for auto-approval to PROVISIONAL status
CAPABILITY_CONFIDENCE_THRESHOLDS = {
    "historical_context": 0.85,      # Higher threshold for historical claims
    "attribution": 0.90,             # Very high for attribution (critical)
    "iconography": 0.80,             # Moderate for visual descriptions
    "provenance_analysis": 0.85,     # Higher for provenance claims
    "die_study": 0.90,               # Very high for die analysis
    "market_analysis": 0.75,         # Lower for market estimates (subjective)
    "conservation": 0.80,            # Moderate for condition assessment
    "default": 0.85,                 # Default threshold for unknown capabilities
}


class LLMFeedbackType(str, Enum):
    """Types of feedback for LLM enrichments."""
    ACCEPTED = "accepted"        # Output was correct as-is
    REJECTED = "rejected"        # Output was incorrect/unusable
    MODIFIED = "modified"        # Output required corrections
    HALLUCINATION = "hallucination"  # Detected factual error


# --- Phase 4: Schema V3 - LLM Architecture Value Objects ---

@dataclass(frozen=True, slots=True)
class LLMEnrichment:
    """
    Centralized LLM enrichment with versioning and quality tracking.

    Replaces inline LLM columns with structured, versioned storage.
    Supports review workflow, cost tracking, and model provenance.
    """
    # Identity
    id: int | None = None
    coin_id: int = 0

    # Capability
    capability: str = ""                  # vocab_normalize, legend_expand, context_generate, etc.
    capability_version: int = 1           # Version of the capability/prompt

    # Model provenance
    model_id: str = ""                    # claude-3-sonnet, gpt-4, gemini-pro, etc.
    model_version: str | None = None      # Specific model version if known

    # Content
    input_hash: str = ""                  # Hash of input for deduplication/caching
    input_snapshot: str | None = None     # JSON snapshot of input data
    output_content: str = ""              # The actual LLM output (JSON or text)
    raw_response: str | None = None       # Full raw API response for debugging

    # Quality
    confidence: float = 0.0               # 0.0-1.0 confidence score
    needs_review: bool = False            # Flagged for human review
    quality_flags: str | None = None      # JSON: ["low_confidence", "multiple_matches", etc.]

    # Cost tracking
    cost_usd: float = 0.0                 # Cost of this API call
    input_tokens: int | None = None       # Input tokens consumed
    output_tokens: int | None = None      # Output tokens generated
    cached: bool = False                  # Was this result from cache?

    # Review workflow
    review_status: str = "pending"        # pending, approved, rejected, superseded
    reviewed_by: str | None = None        # User/system that reviewed
    reviewed_at: DateTimeType | None = None
    review_notes: str | None = None

    # Lifecycle
    created_at: DateTimeType | None = None
    expires_at: DateTimeType | None = None
    superseded_by: int | None = None      # ID of newer enrichment that replaced this
    request_id: str | None = None         # Tracking ID from API provider
    batch_job_id: str | None = None       # Batch job ID if applicable


@dataclass(frozen=True, slots=True)
class PromptTemplate:
    """
    Database-managed prompt template for LLM capabilities.

    Enables versioning, A/B testing, and prompt optimization.
    """
    # Identity
    id: int | None = None
    capability: str = ""                  # Which LLM capability this template is for
    version: int = 1                      # Version number for this capability

    # Content
    system_prompt: str = ""               # System message
    user_template: str = ""               # User message template with {placeholders}
    parameters: str | None = None         # JSON: default parameters, temperature, etc.
    requires_vision: bool = False         # Does this template need image input?
    output_schema: str | None = None      # JSON Schema for expected output

    # A/B testing
    variant_name: str = "default"         # Variant name for A/B testing
    traffic_weight: float = 1.0           # Traffic allocation weight (0.0-1.0)

    # Lifecycle
    is_active: bool = True                # Is this template in use?
    created_at: DateTimeType | None = None
    deprecated_at: DateTimeType | None = None
    notes: str | None = None


@dataclass(frozen=True, slots=True)
class LLMFeedback:
    """
    User feedback on LLM enrichment quality.

    Creates a feedback loop for continuous improvement.
    """
    # Identity
    id: int | None = None
    enrichment_id: int = 0                # Which enrichment this feedback is for

    # Feedback
    feedback_type: str = ""               # accepted, rejected, modified, hallucination
    field_path: str | None = None         # Specific field that was wrong (e.g., "issuer")
    original_value: str | None = None     # What the LLM suggested
    corrected_value: str | None = None    # What it should have been

    # Attribution
    user_id: str | None = None            # Who provided feedback
    feedback_notes: str | None = None     # Additional context

    # Metadata
    created_at: DateTimeType | None = None


@dataclass(frozen=True, slots=True)
class LLMUsageDaily:
    """
    Aggregated LLM usage metrics by day.

    Enables cost monitoring, performance tracking, and capacity planning.
    """
    # Primary key components
    date: str = ""                        # YYYY-MM-DD
    capability: str = ""                  # Which capability
    model_id: str = ""                    # Which model

    # Volume metrics
    request_count: int = 0                # Total requests
    cache_hits: int = 0                   # Requests served from cache
    error_count: int = 0                  # Failed requests

    # Cost metrics
    total_cost_usd: float = 0.0           # Total cost for this day/capability/model
    total_input_tokens: int = 0           # Total input tokens
    total_output_tokens: int = 0          # Total output tokens

    # Quality metrics
    avg_confidence: float | None = None   # Average confidence score
    review_approved: int = 0              # Approved after review
    review_rejected: int = 0              # Rejected after review

    # Performance metrics
    avg_latency_ms: float | None = None   # Average response latency


# --- Phase 5: Schema V3 - Market Tracking & Wishlists ---

@dataclass(slots=True)
class MarketPrice:
    """
    Aggregate market pricing for a coin type by attribution.

    Tracks price statistics across multiple sales/observations
    for coins matching a specific attribution key.
    """
    id: int | None = None
    attribution_key: str = ""
    issuer: str | None = None
    denomination: str | None = None
    mint: str | None = None
    metal: str | None = None
    category: str | None = None  # imperial, republic, provincial, etc.
    catalog_ref: str | None = None
    avg_price_vf: Decimal | None = None
    avg_price_ef: Decimal | None = None
    avg_price_au: Decimal | None = None
    avg_price_ms: Decimal | None = None  # Mint State grade pricing
    min_price_seen: Decimal | None = None
    max_price_seen: Decimal | None = None
    median_price: Decimal | None = None
    data_point_count: int = 0
    last_sale_date: DateType | None = None
    last_updated: DateTimeType | None = None


@dataclass(slots=True)
class MarketDataPoint:
    """
    Individual price observation feeding market aggregates.

    Records single sale/listing events with full context:
    auction results, dealer prices, private sales.
    """
    id: int | None = None
    market_price_id: int | None = None
    price: Decimal = Decimal("0")
    currency: str = "USD"
    price_usd: Decimal | None = None
    source_type: str = ""  # auction_realized, auction_unsold, dealer_asking, dealer_sold, private_sale, estimate
    date: DateType | None = None
    grade: str | None = None
    grade_numeric: int | None = None
    condition_notes: str | None = None
    auction_house: str | None = None
    sale_name: str | None = None
    lot_number: str | None = None
    lot_url: str | None = None
    dealer_name: str | None = None
    # Price breakdown for auction sales
    is_hammer_price: bool = True  # False if price includes buyer's premium
    buyers_premium_pct: Decimal | None = None  # Buyer's premium percentage (e.g., 20.0)
    # Slabbed coin information
    is_slabbed: bool = False
    grading_service: str | None = None  # ngc, pcgs
    certification_number: str | None = None
    confidence: str = "medium"  # low, medium, high, verified
    notes: str | None = None
    created_at: DateTimeType | None = None


@dataclass(slots=True)
class CoinValuation:
    """
    Point-in-time valuation snapshot for a specific coin.

    Tracks purchase price, current market value, and gain/loss
    with trend analysis over time.
    """
    id: int | None = None
    coin_id: int | None = None
    valuation_date: DateType | None = None
    purchase_price: Decimal | None = None
    purchase_currency: str | None = None
    purchase_date: DateType | None = None
    current_market_value: Decimal | None = None
    value_currency: str = "USD"
    market_confidence: str | None = None  # low, medium, high, strong
    comparable_count: int | None = None
    comparable_avg_price: Decimal | None = None
    comparable_date_range: str | None = None
    price_trend_6mo: Decimal | None = None
    price_trend_12mo: Decimal | None = None
    price_trend_36mo: Decimal | None = None
    gain_loss_usd: Decimal | None = None
    gain_loss_pct: Decimal | None = None
    valuation_method: str | None = None  # comparable_sales, dealer_estimate, insurance, user_estimate, llm_estimate
    notes: str | None = None
    created_at: DateTimeType | None = None


@dataclass(slots=True)
class WishlistItem:
    """
    Acquisition target for the collection wishlist.

    Defines matching criteria for desired coins with
    budget constraints and notification preferences.
    """
    id: int | None = None
    title: str = ""
    description: str | None = None
    issuer: str | None = None
    issuer_id: int | None = None
    mint: str | None = None
    mint_id: int | None = None
    year_start: int | None = None
    year_end: int | None = None
    denomination: str | None = None
    metal: str | None = None
    category: str | None = None
    catalog_ref: str | None = None
    catalog_ref_pattern: str | None = None
    min_grade: str | None = None
    min_grade_numeric: int | None = None
    condition_notes: str | None = None
    max_price: Decimal | None = None
    target_price: Decimal | None = None
    currency: str = "USD"
    priority: int = 2  # 1 highest, 4 lowest
    tags: str | None = None  # JSON array
    series_slot_id: int | None = None
    status: str = "wanted"  # wanted, watching, bidding, acquired, cancelled
    acquired_coin_id: int | None = None
    acquired_at: DateTimeType | None = None
    acquired_price: Decimal | None = None
    notify_on_match: bool = True
    notify_email: bool = False
    notes: str | None = None
    created_at: DateTimeType | None = None
    updated_at: DateTimeType | None = None


@dataclass(slots=True)
class PriceAlert:
    """
    User-configured price/availability alert.

    Triggers notifications when price thresholds are met
    or new listings appear matching criteria.
    """
    id: int | None = None
    attribution_key: str | None = None
    coin_id: int | None = None
    wishlist_item_id: int | None = None
    trigger_type: str = ""  # price_below, price_above, price_change_pct, new_listing, auction_soon
    threshold_value: Decimal | None = None
    threshold_pct: Decimal | None = None
    threshold_grade: str | None = None
    status: str = "active"  # active, triggered, paused, expired, deleted
    created_at: DateTimeType | None = None
    triggered_at: DateTimeType | None = None
    expires_at: DateTimeType | None = None
    notification_sent: bool = False
    notification_sent_at: DateTimeType | None = None
    notification_channel: str | None = None  # in_app, email, push
    cooldown_hours: int = 24
    last_triggered_at: DateTimeType | None = None
    notes: str | None = None


# --- Phase 6: Schema V3 - Collections Enums ---

class CollectionType(str, Enum):
    """Type of collection."""
    CUSTOM = "custom"         # Manual coin selection
    SMART = "smart"           # Dynamic based on criteria
    SERIES = "series"         # Linked to a series definition
    TYPE_SET = "type_set"     # Completion-tracking type set


class CollectionPurpose(str, Enum):
    """Purpose classification for collections (numismatic workflow)."""
    STUDY = "study"           # Research/educational grouping
    DISPLAY = "display"       # Exhibition arrangement
    TYPE_SET = "type_set"     # Systematic completion goal
    DUPLICATES = "duplicates" # Trading stock
    RESERVES = "reserves"     # Secondary examples
    INSURANCE = "insurance"   # Documentation grouping
    GENERAL = "general"       # Default/unclassified


class StandardSortOrder(str, Enum):
    """Predefined sort orders for collections."""
    CHRONOLOGICAL = "chronological"
    REVERSE_CHRONOLOGICAL = "reverse_chronological"
    CATALOG_NUMBER = "catalog_number"
    ACQUISITION_DATE = "acquisition_date"
    VALUE_HIGH_LOW = "value_desc"
    VALUE_LOW_HIGH = "value_asc"
    WEIGHT = "weight"
    DENOMINATION = "denomination"
    CUSTOM = "custom"


# --- Phase 6: Schema V3 - Collections Value Objects ---

@dataclass(frozen=True, slots=True)
class SmartCriteria:
    """
    Value object for smart collection filter criteria.

    Supports compound conditions with 'all' (AND) or 'any' (OR) matching.
    Each condition specifies a field, operator, and value.
    """
    match: str = "all"  # "all" (AND) or "any" (OR)
    conditions: tuple = ()  # Tuple of condition dicts for immutability

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for JSON storage."""
        return {
            "match": self.match,
            "conditions": list(self.conditions)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SmartCriteria":
        """Deserialize from dictionary."""
        if not data:
            return cls()
        return cls(
            match=data.get("match", "all"),
            conditions=tuple(data.get("conditions", []))
        )


@dataclass(frozen=True, slots=True)
class CollectionStatistics:
    """
    Computed statistics for a collection.

    Provides portfolio-style analytics for collectors.
    """
    coin_count: int = 0
    total_value: Decimal | None = None
    total_cost: Decimal | None = None
    unrealized_gain_loss: Decimal | None = None
    metal_breakdown: Dict[str, int] | None = None
    denomination_breakdown: Dict[str, int] | None = None
    category_breakdown: Dict[str, int] | None = None
    grade_distribution: Dict[str, int] | None = None
    average_grade: float | None = None
    slabbed_count: int = 0
    raw_count: int = 0
    earliest_coin_year: int | None = None
    latest_coin_year: int | None = None
    completion_percentage: float | None = None  # For type sets
    missing_types: List[str] | None = None  # For type sets


# --- Phase 6: Schema V3 - Collections Entities ---

@dataclass(slots=True)
class Collection:
    """
    Collection entity for organizing coins.

    Supports custom (manual) and smart (dynamic) collections with
    hierarchical nesting limited to 3 levels per numismatic review.
    """
    id: int | None = None
    name: str = ""
    description: str | None = None
    slug: str | None = None

    # Type and purpose
    collection_type: str = "custom"  # custom, smart, series, type_set
    purpose: str = "general"  # study, display, type_set, duplicates, reserves, insurance, general

    # Smart collection criteria
    smart_criteria: SmartCriteria | None = None

    # Type set tracking (for completion percentage)
    is_type_set: bool = False
    type_set_definition: str | None = None  # JSON defining required types

    # Visual settings
    cover_image_url: str | None = None
    cover_coin_id: int | None = None  # Featured coin as cover
    color: str | None = None  # UI color code
    icon: str | None = None  # Icon identifier

    # Organization
    parent_id: int | None = None
    level: int = 0  # Hierarchy depth (max 3 per review)
    display_order: int = 0
    default_sort: str = "custom"  # StandardSortOrder value
    default_view: str | None = None  # grid, list, table

    # Cached statistics
    coin_count: int = 0
    total_value: Decimal | None = None
    stats_updated_at: DateTimeType | None = None
    completion_percentage: float | None = None  # For type sets

    # Flags
    is_favorite: bool = False
    is_hidden: bool = False
    is_public: bool = False

    # Physical storage mapping (from numismatic review)
    storage_location: str | None = None  # "Album 3, Page 12"

    # Metadata
    notes: str | None = None
    created_at: DateTimeType | None = None
    updated_at: DateTimeType | None = None

    def __post_init__(self):
        """Validate collection data."""
        if not self.name or not self.name.strip():
            raise ValueError("Collection name cannot be empty")
        if self.collection_type == "smart" and not self.smart_criteria:
            # Smart collections should have criteria, but allow creation without
            pass
        if self.level is not None and self.level > 3:
            raise ValueError("Collection hierarchy limited to 3 levels")


@dataclass(slots=True)
class CollectionCoin:
    """
    Link between a collection and a coin with per-collection context.

    Allows adding notes and flags specific to a coin's presence
    in a particular collection.
    """
    collection_id: int
    coin_id: int
    added_at: DateTimeType | None = None
    added_by: str | None = None

    # Ordering
    position: int | None = None
    custom_order: int | None = None

    # Context notes (per-collection)
    notes: str | None = None

    # Flags (from numismatic review)
    is_featured: bool = False  # Highlight coin in collection
    is_cover_coin: bool = False  # Use as collection thumbnail
    is_placeholder: bool = False  # Temporary until upgrade
    exclude_from_stats: bool = False  # Don't count in totals

    # Type set tracking
    fulfills_type: str | None = None  # Which type requirement this satisfies
    series_slot_id: int | None = None  # Link to series slot if applicable


@dataclass(slots=True)
class WishlistMatch:
    """
    Matched auction lot or listing for a wishlist item.

    Records potential acquisitions found by the matching
    engine with scoring and notification tracking.
    """
    id: int | None = None
    wishlist_item_id: int | None = None
    match_type: str = ""  # auction_lot, dealer_listing, ebay_listing, vcoins
    match_source: str | None = None  # heritage, cng, biddr, ebay, vcoins
    match_id: str = ""
    match_url: str | None = None
    title: str = ""
    description: str | None = None
    image_url: str | None = None
    grade: str | None = None
    grade_numeric: int | None = None
    condition_notes: str | None = None
    price: Decimal | None = None
    estimate_low: Decimal | None = None
    estimate_high: Decimal | None = None
    currency: str = "USD"
    current_bid: Decimal | None = None
    auction_date: DateType | None = None
    end_time: DateTimeType | None = None
    match_score: Decimal | None = None
    match_confidence: str | None = None  # exact, high, medium, possible
    match_reasons: str | None = None  # JSON array
    is_below_budget: bool | None = None
    is_below_market: bool | None = None
    value_score: Decimal | None = None
    notified: bool = False
    notified_at: DateTimeType | None = None
    dismissed: bool = False
    dismissed_at: DateTimeType | None = None
    saved: bool = False
    notes: str | None = None
    created_at: DateTimeType | None = None


# --- Aggregate Root ---

@dataclass
class Coin:
    id: int | None
    category: Category
    metal: Metal
    dimensions: Dimensions
    attribution: Attribution
    grading: GradingDetails
    acquisition: AcquisitionDetails | None = None
    description: str | None = None
    images: List[CoinImage] = field(default_factory=list)
    # New fields from expert review
    denomination: str | None = None              # "denarius", "antoninianus", "sestertius"
    portrait_subject: str | None = None          # When different from issuer (e.g., heir, empress)
    design: Design | None = None                 # Legends and descriptions
    references: List[CatalogReference] = field(default_factory=list)  # RIC, Crawford, etc.
    provenance: List[ProvenanceEntry] = field(default_factory=list)   # Ownership history
    
    # --- Research Grade Extensions ---
    issue_status: IssueStatus = IssueStatus.OFFICIAL
    die_info: DieInfo | None = None
    monograms: List[Monogram] = field(default_factory=list)
    secondary_treatments: List[Dict[str, Any]] | None = None # JSON structure
    find_data: FindData | None = None

    # Collection management
    storage_location: str | None = None          # Physical location (e.g., "SlabBox1", "Velv2-5-1")
    personal_notes: str | None = None            # Owner notes, observations, research
    # Rarity (numismatic)
    rarity: str | None = None                     # RIC-style code: C, S, R1-R5, RR, RRR, UNIQUE
    rarity_notes: str | None = None              # Source or description

    # LLM enrichment
    enrichment: EnrichmentData | None = None

    # --- Phase 1: Schema V3 Numismatic Enhancements ---
    # Attribution enhancements
    secondary_authority: SecondaryAuthority | None = None
    co_ruler: CoRuler | None = None
    moneyer_gens: str | None = None              # Republican moneyer family

    # Physical enhancements
    physical_enhancements: PhysicalEnhancements | None = None

    # Secondary treatments
    secondary_treatments_v3: SecondaryTreatments | None = None

    # Tooling/Repairs
    tooling_repairs: ToolingRepairs | None = None

    # Centering
    centering_info: Centering | None = None

    # Die study enhancements (extends die_info)
    die_study: DieStudyEnhancements | None = None

    # Grading TPG enhancements (extends grading)
    grading_tpg: GradingTPGEnhancements | None = None

    # Chronology enhancements
    chronology: ChronologyEnhancements | None = None

    def is_dated(self) -> bool:
        return self.attribution.year_start is not None

    def update_dimensions(self, new_dimensions: Dimensions):
        self.dimensions = new_dimensions
    
    def add_image(self, url: str, image_type: str, is_primary: bool = False):
        if is_primary:
            # Unset primary flag on all existing images by creating new instances
            # (CoinImage is frozen, so we must replace rather than modify)
            self.images = [
                CoinImage(img.url, img.image_type, is_primary=False)
                for img in self.images
            ]
        self.images.append(CoinImage(url, image_type, is_primary))
    
    @property
    def primary_image(self) -> CoinImage | None:
        for img in self.images:
            if img.is_primary:
                return img
        return self.images[0] if self.images else None