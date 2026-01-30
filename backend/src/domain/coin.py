from dataclasses import dataclass, field
from typing import List, Dict, Any, Self
from datetime import date as DateType
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

@dataclass(frozen=True, slots=True)
class ProvenanceEntry:
    """A single provenance event in a coin's ownership history."""
    source_type: str          # "collection", "auction", "dealer", "private_sale"
    source_name: str          # "Hunt Collection", "Heritage", "CNG"
    event_date: DateType | None = None
    lot_number: str | None = None
    notes: str | None = None
    raw_text: str = ""

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