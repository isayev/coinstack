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