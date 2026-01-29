from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import date
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

@dataclass(frozen=True)
class Dimensions:
    weight_g: Decimal
    diameter_mm: Decimal
    die_axis: Optional[int] = None
    specific_gravity: Optional[Decimal] = None

    def __post_init__(self):
        if self.weight_g < 0:
            raise ValueError("Weight must be positive")
        if self.diameter_mm < 0:
            raise ValueError("Diameter must be positive")
        if self.die_axis is not None and not (0 <= self.die_axis <= 12):
            raise ValueError("Die axis must be between 0 and 12")

@dataclass(frozen=True)
class Attribution:
    issuer: str
    issuer_id: Optional[int] = None
    mint: Optional[str] = None
    mint_id: Optional[int] = None
    year_start: Optional[int] = None
    year_end: Optional[int] = None

@dataclass(frozen=True)
class GradingDetails:
    grading_state: GradingState
    grade: str
    service: Optional[GradeService] = None
    certification_number: Optional[str] = None
    strike: Optional[str] = None
    surface: Optional[str] = None

    def __post_init__(self):
        if self.grading_state == GradingState.SLABBED and not self.service:
            raise ValueError("Slabbed coins must have a grading service specified")

@dataclass(frozen=True)
class AcquisitionDetails:
    price: Decimal
    currency: str
    source: str
    date: Optional[date] = None
    url: Optional[str] = None

    def __post_init__(self):
        if self.price < 0:
            raise ValueError("Price cannot be negative")

@dataclass(frozen=True)
class Design:
    """Coin design details - legends, descriptions, and exergue text."""
    obverse_legend: Optional[str] = None       # "IMP CAES DOMIT AVG GERM COS XVI..."
    obverse_description: Optional[str] = None  # "laureate head of Domitian right"
    reverse_legend: Optional[str] = None       # "MONETA AVGVSTI"
    reverse_description: Optional[str] = None  # "Moneta standing left, holding scales"
    exergue: Optional[str] = None              # Text below main reverse design

@dataclass(frozen=True)
class CatalogReference:
    """A single catalog reference for a coin."""
    catalog: str              # "RIC", "Crawford", "Sear", "RSC", "RPC", "BMC", "SNG"
    number: str               # "756", "44/5", "1234a" (may include variant e.g. 351b)
    volume: Optional[str] = None   # "II", "V.1", etc. (Roman for RIC/RPC)
    suffix: Optional[str] = None   # Additional qualifiers
    raw_text: str = ""        # Original text as found
    is_primary: bool = False  # Primary reference for this coin
    notes: Optional[str] = None  # Additional notes about this reference
    source: Optional[str] = None   # "user" | "import" | "scraper" | "llm_approved" | "catalog_lookup"
    # Optional catalog-specific fields (backward compatible)
    variant: Optional[str] = None   # e.g. "a", "b" (RIC, Crawford, DOC)
    mint: Optional[str] = None     # RIC VI+ mint code, BMCRR/BMC Greek
    supplement: Optional[str] = None  # RPC "S", "S2"
    collection: Optional[str] = None  # SNG collection (e.g. "Copenhagen", "ANS")

@dataclass(frozen=True)
class ProvenanceEntry:
    """A single provenance event in a coin's ownership history."""
    source_type: str          # "collection", "auction", "dealer", "private_sale"
    source_name: str          # "Hunt Collection", "Heritage", "CNG"
    event_date: Optional[date] = None
    lot_number: Optional[str] = None
    notes: Optional[str] = None
    raw_text: str = ""

@dataclass(frozen=True)
class CoinImage:
    """Represents an image of the coin."""
    url: str
    image_type: str # 'obverse', 'reverse', 'slab', etc.
    is_primary: bool = False

@dataclass(frozen=True)
class Monogram:
    """Represents a Monogram linked to a coin."""
    id: Optional[int]
    label: str
    image_url: Optional[str] = None
    vector_data: Optional[str] = None

@dataclass(frozen=True)
class DieInfo:
    """Research-grade die study information."""
    obverse_die_id: Optional[str] = None
    reverse_die_id: Optional[str] = None

@dataclass(frozen=True)
class FindData:
    """Archaeological context or find data."""
    find_spot: Optional[str] = None
    find_date: Optional[date] = None

# --- Aggregate Root ---

@dataclass
class Coin:
    id: Optional[int]
    category: Category
    metal: Metal
    dimensions: Dimensions
    attribution: Attribution
    grading: GradingDetails
    acquisition: Optional[AcquisitionDetails] = None
    description: Optional[str] = None
    images: List[CoinImage] = field(default_factory=list)
    # New fields from expert review
    denomination: Optional[str] = None              # "denarius", "antoninianus", "sestertius"
    portrait_subject: Optional[str] = None          # When different from issuer (e.g., heir, empress)
    design: Optional[Design] = None                 # Legends and descriptions
    references: List[CatalogReference] = field(default_factory=list)  # RIC, Crawford, etc.
    provenance: List[ProvenanceEntry] = field(default_factory=list)   # Ownership history
    
    # --- Research Grade Extensions ---
    issue_status: IssueStatus = IssueStatus.OFFICIAL
    die_info: Optional[DieInfo] = None
    monograms: List[Monogram] = field(default_factory=list)
    secondary_treatments: Optional[List[Dict[str, Any]]] = None # JSON structure
    find_data: Optional[FindData] = None

    # Collection management
    storage_location: Optional[str] = None          # Physical location (e.g., "SlabBox1", "Velv2-5-1")
    personal_notes: Optional[str] = None            # Owner notes, observations, research
    # Rarity (numismatic)
    rarity: Optional[str] = None                     # RIC-style code: C, S, R1-R5, RR, RRR, UNIQUE
    rarity_notes: Optional[str] = None              # Source or description

    # LLM enrichment
    historical_significance: Optional[str] = None   # LLM-generated historical context
    llm_enriched_at: Optional[str] = None           # Timestamp of last LLM enrichment
    llm_analysis_sections: Optional[str] = None     # JSON-encoded analysis sections
    llm_suggested_references: Optional[List[str]] = None  # Citations found by LLM for audit
    llm_suggested_rarity: Optional[Dict[str, Any]] = None  # Rarity info from LLM for audit
    llm_suggested_design: Optional[Dict[str, Any]] = None   # Design suggestions: obverse_legend, reverse_legend, exergue, obverse_description, reverse_description, *_expanded
    llm_suggested_attribution: Optional[Dict[str, Any]] = None  # Attribution suggestions: issuer, mint, denomination, year_start, year_end

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
    def primary_image(self) -> Optional[CoinImage]:
        for img in self.images:
            if img.is_primary:
                return img
        return self.images[0] if self.images else None