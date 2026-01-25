# Domain Entities & Value Objects

## Overview

The Domain layer contains pure business entities with no dependencies on frameworks or infrastructure. Entities are mutable and have identity, while Value Objects are immutable and defined by their attributes.

## Core Entities

### Coin (Aggregate Root)

**Location**: `src/domain/coin.py`

**Purpose**: Central domain entity representing a physical ancient coin in the collection.

**Key Characteristics**:
- Aggregate Root: Manages consistency of coin data and related entities (images, references)
- Identity: Unique coin ID
- Lifecycle: Created, modified, audited, potentially deleted
- Invariants: Business rules for valid coin state

**Structure**:
```python
@dataclass
class Coin:
    # Identity
    id: Optional[int]

    # Classification (REQUIRED)
    category: str          # republic, imperial, provincial, byzantine, greek, other
    denomination: str      # Denarius, Aureus, Antoninianus, Solidus, etc.
    metal: str            # gold, silver, bronze, billon, electrum, orichalcum

    # Attribution (WHO issued the coin)
    issuing_authority: Optional[str]   # "Augustus", "Trajan", "Rome"
    portrait_subject: Optional[str]    # May differ from issuer
    dynasty: Optional[str]             # "Julio-Claudian", "Flavian"
    status: Optional[str]              # "Augustus", "Caesar", "Usurper"

    # Chronology (WHEN minted)
    reign_start: Optional[int]         # Year (negative for BC)
    reign_end: Optional[int]
    mint_year_start: Optional[int]
    mint_year_end: Optional[int]

    # Geography (WHERE minted)
    mint: Optional[str]               # "Rome", "Antioch", "Alexandria"

    # Physical Characteristics
    weight_g: Optional[Decimal]       # Weight in grams
    diameter_mm: Optional[Decimal]    # Diameter in millimeters
    die_axis: Optional[int]           # 0-12 (clock positions)

    # Design & Iconography
    obverse_legend: Optional[str]     # Text on front
    obverse_description: Optional[str]
    reverse_legend: Optional[str]     # Text on back
    reverse_description: Optional[str]
    exergue: Optional[str]            # Text below main design

    # Grading & Certification
    grade_service: Optional[str]      # ngc, pcgs, self, dealer
    grade: Optional[str]              # "Ch VF", "MS 5/5 4/5", etc.
    certification_number: Optional[str]

    # Acquisition
    acquisition_date: Optional[date]
    acquisition_price: Optional[Decimal]
    acquisition_source: Optional[str]
    acquisition_url: Optional[str]

    # Storage & Organization
    holder_type: Optional[str]        # "slab", "flip", "album"
    storage_location: Optional[str]

    # Research & Notes
    rarity: Optional[str]             # common, scarce, rare, very_rare, extremely_rare, unique
    historical_significance: Optional[str]
    personal_notes: Optional[str]

    # Related Entities (Collections)
    images: List['CoinImage'] = field(default_factory=list)
    references: List['CoinReference'] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    # Value Objects (Encapsulation)
    dimensions: Optional['Dimensions'] = None
    attribution: Optional['Attribution'] = None
    grading_details: Optional['GradingDetails'] = None
    acquisition_details: Optional['AcquisitionDetails'] = None
```

**Business Rules** (Invariants):
- `category` must be one of valid enum values
- `metal` must be one of valid enum values
- `weight_g` if present must be > 0
- `diameter_mm` if present must be > 0
- `die_axis` if present must be 0-12
- `reign_start <= reign_end` (if both present)
- `mint_year_start <= mint_year_end` (if both present)
- BC years are negative integers

**Methods**:
```python
def validate(self) -> List[str]:
    """Returns list of validation errors."""
    errors = []
    if self.weight_g and self.weight_g <= 0:
        errors.append("Weight must be positive")
    if self.diameter_mm and self.diameter_mm <= 0:
        errors.append("Diameter must be positive")
    # ... more validations
    return errors

def is_imperial(self) -> bool:
    """Check if coin is Roman Imperial category."""
    return self.category == "imperial"

def is_graded(self) -> bool:
    """Check if coin is professionally graded."""
    return self.grade_service in ["ngc", "pcgs"]
```

### AuctionLot

**Location**: `src/domain/auction.py`

**Purpose**: Represents auction lot data scraped from auction houses.

**Structure**:
```python
@dataclass
class AuctionLot:
    # Identity
    url: str                          # Unique identifier

    # Auction Metadata
    auction_house: str                # "Heritage", "CNG", "Biddr"
    lot_number: Optional[str]
    sale_name: Optional[str]
    sale_date: Optional[date]

    # Classification (same as Coin)
    category: Optional[str]
    denomination: Optional[str]
    metal: Optional[str]

    # Attribution
    issuing_authority: Optional[str]
    portrait_subject: Optional[str]

    # Chronology
    mint_year_start: Optional[int]
    mint_year_end: Optional[int]

    # Physical
    weight_g: Optional[Decimal]
    diameter_mm: Optional[Decimal]

    # Design
    obverse_description: Optional[str]
    reverse_description: Optional[str]

    # Grading & Price
    grade: Optional[str]
    price_realized: Optional[Decimal]
    estimate_min: Optional[Decimal]
    estimate_max: Optional[Decimal]

    # References & Images
    references: List[str] = field(default_factory=list)
    image_urls: List[str] = field(default_factory=list)

    # Provenance
    provenance: Optional[str]         # Ownership history

    # Full description
    description: Optional[str]
```

**Usage**:
- Scrapers produce `AuctionLot` entities
- Audit system compares `Coin` against `AuctionLot` data
- Import system converts `AuctionLot` to `Coin`

### Series

**Location**: `src/domain/series.py`

**Purpose**: Groups coins by ruler/type/period for collection organization.

**Structure**:
```python
@dataclass
class Series:
    # Identity
    id: Optional[int]
    slug: str                         # URL-friendly unique identifier

    # Core Info
    name: str                         # "Augustus Denarii"
    category: str                     # imperial, republic, etc.

    # Description
    description: Optional[str]
    historical_context: Optional[str]

    # Metadata
    coin_count: int = 0               # Number of coins in series
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
```

**Examples**:
- "Julius Caesar Denarii" (slug: `julius-caesar-denarii`)
- "Trajan Provincial Bronze" (slug: `trajan-provincial-bronze`)
- "Byzantine Gold Solidi" (slug: `byzantine-gold-solidi`)

### VocabTerm

**Location**: `src/domain/vocab.py`

**Purpose**: Controlled vocabulary for consistent data entry (issuing authorities, mints, etc.).

**Structure**:
```python
@dataclass
class VocabTerm:
    # Identity
    id: Optional[int]
    term_type: str                    # "issuer", "mint", "ruler"

    # Core Data
    canonical_name: str               # "Augustus"
    display_name: Optional[str]       # "Caesar Augustus"

    # Variants & Aliases
    variants: List[str] = field(default_factory=list)  # ["Octavian", "Octavianus"]

    # Metadata
    category: Optional[str]           # imperial, republic, etc.
    start_year: Optional[int]
    end_year: Optional[int]

    # Usage Stats
    coin_count: int = 0               # How many coins use this term
```

**Examples**:
- Issuer: `canonical_name="Augustus"`, `variants=["Octavian", "Octavianus"]`
- Mint: `canonical_name="Rome"`, `variants=["Roma"]`
- Ruler: `canonical_name="Trajan"`, `variants=["Marcus Ulpius Traianus"]`

## Value Objects

Value Objects are **immutable** objects defined by their attributes (no identity). Two value objects with same attributes are considered equal.

### Dimensions

**Location**: `src/domain/coin.py`

**Purpose**: Encapsulates physical measurements of coin.

```python
@dataclass(frozen=True)
class Dimensions:
    weight_g: Optional[Decimal]
    diameter_mm: Optional[Decimal]
    die_axis: Optional[int]

    def __post_init__(self):
        """Validation on construction."""
        if self.weight_g and self.weight_g <= 0:
            raise ValueError("Weight must be positive")
        if self.diameter_mm and self.diameter_mm <= 0:
            raise ValueError("Diameter must be positive")
        if self.die_axis and not (0 <= self.die_axis <= 12):
            raise ValueError("Die axis must be 0-12")

    def is_complete(self) -> bool:
        """Check if all dimensions are present."""
        return all([self.weight_g, self.diameter_mm, self.die_axis])
```

**Usage**:
```python
dims = Dimensions(weight_g=Decimal("3.45"), diameter_mm=Decimal("19.2"), die_axis=6)
coin.dimensions = dims
```

### Attribution

**Location**: `src/domain/coin.py`

**Purpose**: Encapsulates coin attribution (who issued it).

```python
@dataclass(frozen=True)
class Attribution:
    issuing_authority: Optional[str]
    portrait_subject: Optional[str]
    dynasty: Optional[str]
    status: Optional[str]

    def is_complete(self) -> bool:
        """Check if key attribution fields are present."""
        return bool(self.issuing_authority and self.portrait_subject)

    def matches(self, other: 'Attribution') -> bool:
        """Check if attributions match (fuzzy matching)."""
        return (
            self.issuing_authority == other.issuing_authority and
            self.portrait_subject == other.portrait_subject
        )
```

### GradingDetails

**Location**: `src/domain/coin.py`

**Purpose**: Encapsulates grading information.

```python
@dataclass(frozen=True)
class GradingDetails:
    service: str                      # ngc, pcgs, self, dealer
    grade: str                        # "Ch VF", "MS 5/5 4/5"
    certification_number: Optional[str]

    def is_professional(self) -> bool:
        """Check if professionally graded."""
        return self.service in ["ngc", "pcgs"]

    def is_certified(self) -> bool:
        """Check if has certification number."""
        return bool(self.certification_number)
```

### AcquisitionDetails

**Location**: `src/domain/coin.py`

**Purpose**: Encapsulates acquisition information.

```python
@dataclass(frozen=True)
class AcquisitionDetails:
    date: Optional[date]
    price: Optional[Decimal]
    source: Optional[str]             # "Heritage Auctions", "VCoins"
    url: Optional[str]

    def is_complete(self) -> bool:
        """Check if all acquisition fields are present."""
        return all([self.date, self.price, self.source])

    def is_recent(self, days: int = 30) -> bool:
        """Check if acquired within N days."""
        if not self.date:
            return False
        delta = date.today() - self.date
        return delta.days <= days
```

## Enums

**Location**: `src/domain/coin.py`

**Purpose**: Constrained string values for classification fields.

### Category
```python
class Category(str, Enum):
    REPUBLIC = "republic"
    IMPERIAL = "imperial"
    PROVINCIAL = "provincial"
    BYZANTINE = "byzantine"
    GREEK = "greek"
    CELTIC = "celtic"
    JUDAEAN = "judaean"
    OTHER = "other"
```

### Metal
```python
class Metal(str, Enum):
    GOLD = "gold"           # AU
    SILVER = "silver"       # AR
    BILLON = "billon"       # Debased silver
    BRONZE = "bronze"       # AE
    ELECTRUM = "electrum"   # Gold-silver alloy
    ORICHALCUM = "orichalcum"  # Brass-like
    POTIN = "potin"         # Bronze-tin alloy
    LEAD = "lead"
    AE = "ae"              # Generic ancient bronze
```

### Rarity
```python
class Rarity(str, Enum):
    COMMON = "common"
    SCARCE = "scarce"
    RARE = "rare"
    VERY_RARE = "very_rare"
    EXTREMELY_RARE = "extremely_rare"
    UNIQUE = "unique"
```

### GradeService
```python
class GradeService(str, Enum):
    NGC = "ngc"
    PCGS = "pcgs"
    SELF = "self"
    DEALER = "dealer"
```

## Related Entities

### CoinImage

**Location**: `src/domain/coin.py`

**Purpose**: Stores image metadata for coin photos.

```python
@dataclass
class CoinImage:
    id: Optional[int]
    coin_id: int
    image_type: str               # "obverse", "reverse", "edge", "slab"
    file_path: str
    perceptual_hash: Optional[str]  # For duplicate detection
    width: Optional[int]
    height: Optional[int]
```

### CoinReference

**Location**: `src/domain/coin.py`

**Purpose**: Links coin to catalog references (RIC, RPC, Crawford).

```python
@dataclass
class CoinReference:
    id: Optional[int]
    coin_id: int
    reference_type: str           # "RIC", "RPC", "Crawford", "Sear"
    reference_text: str           # "RIC I 207", "Crawford 335/1c"
    volume: Optional[str]         # "I", "II"
    page: Optional[str]
    number: Optional[str]         # "207", "335/1c"
```

**Example References**:
- `RIC I 207` → `reference_type="RIC"`, `volume="I"`, `number="207"`
- `Crawford 335/1c` → `reference_type="Crawford"`, `number="335/1c"`
- `RPC I 3201` → `reference_type="RPC"`, `volume="I"`, `number="3201"`

## Domain Services

Domain services contain business logic that doesn't naturally belong to a single entity.

### AuditEngine

**Location**: `src/domain/services/audit_engine.py`

**Purpose**: Compares coin against reference data using pluggable strategies.

```python
class AuditEngine:
    def __init__(self, strategies: List[AuditStrategy]):
        self.strategies = strategies

    def audit_coin(self, coin: Coin, reference: AuctionLot) -> AuditReport:
        """Run all audit strategies and aggregate results."""
        results = []
        for strategy in self.strategies:
            result = strategy.check(coin, reference)
            results.append(result)

        return AuditReport(
            coin_id=coin.id,
            reference_url=reference.url,
            checks=results,
            overall_status=self._aggregate_status(results)
        )
```

### SearchService

**Location**: `src/domain/services/search_service.py`

**Purpose**: Full-text search and filtering of coins.

```python
class SearchService:
    def search(
        self,
        query: str,
        category: Optional[str] = None,
        metal: Optional[str] = None,
        **filters
    ) -> List[Coin]:
        """Search coins with filters."""
        # Implementation delegates to repository
        pass
```

---

**Next:** [05-DATA-MODEL.md](05-DATA-MODEL.md) - Database schema and ORM models
