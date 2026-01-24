# Backend Modules Reference

## Directory Structure

```
backend/app/
├── main.py              # FastAPI application entry
├── config.py            # Settings and configuration
├── database.py          # SQLAlchemy setup
├── models/              # ORM models
├── schemas/             # Pydantic schemas
├── routers/             # API endpoints
├── crud/                # Database operations
└── services/            # Business logic
```

---

## Core Application Files

### `main.py`

FastAPI application setup with middleware and router registration.

```python
# Key components:
- app = FastAPI() instance
- CORS middleware configuration
- Exception handlers
- Router includes for all API modules
```

**Registered Routers:**
- `/api/coins` - Coin CRUD
- `/api/import` - Import operations
- `/api/stats` - Collection statistics
- `/api/settings` - Database/backup
- `/api/catalog` - Reference lookups
- `/api/auctions` - Auction data
- `/api/scrape` - URL scraping
- `/api/audit` - Audit system
- `/api/campaign` - Enrichment campaigns
- `/api/legend` - Legend expansion

### `config.py`

Pydantic Settings for environment configuration.

```python
class Settings(BaseSettings):
    database_url: str = "sqlite:///./data/coinstack.db"
    anthropic_api_key: str | None = None
    log_level: str = "INFO"
    upload_dir: str = "./uploads"
    # Scraper config
    scraper_rate_limit: float = 1.0
    scraper_timeout: int = 30
```

### `database.py`

SQLAlchemy engine and session management.

```python
# Key exports:
- engine: SQLAlchemy Engine
- SessionLocal: Session factory
- Base: DeclarativeBase for models
- get_db(): Dependency for request sessions
```

---

## Models (`app/models/`)

### Core Models

#### `coin.py`

Main Coin model with all numismatic fields.

```python
class Coin(Base):
    __tablename__ = "coins"
    
    # Identity
    id: Mapped[int]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    
    # Classification
    category: Mapped[Category]          # Enum: republic, imperial, etc.
    denomination: Mapped[str | None]
    metal: Mapped[Metal | None]         # Enum: gold, silver, etc.
    series: Mapped[str | None]
    
    # Attribution
    issuing_authority: Mapped[str | None]   # Who issued
    portrait_subject: Mapped[str | None]    # Who depicted
    status: Mapped[str | None]              # Augustus, Caesar, etc.
    
    # Chronology
    reign_start: Mapped[int | None]     # Negative for BC
    reign_end: Mapped[int | None]
    mint_year_start: Mapped[int | None]
    mint_year_end: Mapped[int | None]
    dating_certainty: Mapped[DatingCertainty | None]
    
    # Physical
    weight_g: Mapped[Decimal | None]
    diameter_mm: Mapped[Decimal | None]
    die_axis: Mapped[int | None]        # 1-12 clock hours
    
    # Design
    obverse_legend: Mapped[str | None]
    obverse_description: Mapped[str | None]
    reverse_legend: Mapped[str | None]
    reverse_description: Mapped[str | None]
    exergue: Mapped[str | None]
    
    # Grading
    grade_service: Mapped[GradeService | None]
    grade: Mapped[str | None]
    certification_number: Mapped[str | None]
    holder_type: Mapped[HolderType | None]
    
    # Acquisition
    acquisition_date: Mapped[date | None]
    acquisition_price: Mapped[Decimal | None]
    acquisition_source: Mapped[str | None]
    acquisition_url: Mapped[str | None]
    
    # Collection
    storage_location: Mapped[str | None]
    current_value: Mapped[Decimal | None]
    rarity: Mapped[Rarity | None]
    historical_significance: Mapped[str | None]
    personal_notes: Mapped[str | None]
    
    # Relationships
    mint_id: Mapped[int | None]  # FK to Mint
    mint: Mapped["Mint"]
    references: Mapped[list["CoinReference"]]
    images: Mapped[list["CoinImage"]]
    provenance_events: Mapped[list["ProvenanceEvent"]]
    tags: Mapped[list["CoinTag"]]
    countermarks: Mapped[list["Countermark"]]
    auction_data: Mapped[list["AuctionData"]]
```

**Enums in coin.py:**

```python
class Category(str, Enum):
    republic = "republic"
    imperial = "imperial"
    provincial = "provincial"
    byzantine = "byzantine"
    greek = "greek"
    other = "other"

class Metal(str, Enum):
    gold = "gold"
    silver = "silver"
    billon = "billon"
    bronze = "bronze"
    orichalcum = "orichalcum"
    copper = "copper"

class Rarity(str, Enum):
    common = "common"
    scarce = "scarce"
    rare = "rare"
    very_rare = "very_rare"
    extremely_rare = "extremely_rare"
    unique = "unique"

class GradeService(str, Enum):
    ngc = "ngc"
    pcgs = "pcgs"
    self = "self"
    dealer = "dealer"

class HolderType(str, Enum):
    slab = "slab"
    flip = "flip"
    envelope = "envelope"
    raw = "raw"
```

#### `mint.py`

Mint location model.

```python
class Mint(Base):
    __tablename__ = "mints"
    
    id: Mapped[int]
    name: Mapped[str]           # "Rome", "Lugdunum"
    ancient_name: Mapped[str | None]
    modern_name: Mapped[str | None]
    region: Mapped[str | None]
    country: Mapped[str | None]
    latitude: Mapped[float | None]
    longitude: Mapped[float | None]
    
    coins: Mapped[list["Coin"]]
```

#### `reference.py`

Catalog reference citations.

```python
class CoinReference(Base):
    __tablename__ = "coin_references"
    
    id: Mapped[int]
    coin_id: Mapped[int]        # FK to Coin
    reference_type_id: Mapped[int | None]  # FK to ReferenceType
    
    system: Mapped[str]         # "RIC", "Crawford", "RPC"
    volume: Mapped[str | None]  # "I", "VII"
    number: Mapped[str]         # "207", "335/1"
    page: Mapped[str | None]
    plate: Mapped[str | None]
    variation: Mapped[str | None]
    note: Mapped[str | None]
    
    # Lookup status
    lookup_attempted: Mapped[bool]
    lookup_success: Mapped[bool]
    lookup_data: Mapped[dict | None]  # JSON from catalog API
```

#### `image.py`

Coin image storage with deduplication.

```python
class CoinImage(Base):
    __tablename__ = "coin_images"
    
    id: Mapped[int]
    coin_id: Mapped[int]
    
    image_type: Mapped[ImageType]  # obverse, reverse, combined, detail
    file_path: Mapped[str]
    original_filename: Mapped[str | None]
    mime_type: Mapped[str | None]
    
    # Perceptual hash for deduplication
    phash: Mapped[str | None]
    
    # Ordering
    sort_order: Mapped[int]
    is_primary: Mapped[bool]
```

### Auction Models

#### `auction_data.py`

Auction records linked to coins.

```python
class AuctionData(Base):
    __tablename__ = "auction_data"
    
    id: Mapped[int]
    coin_id: Mapped[int | None]     # FK to Coin (nullable)
    
    # Auction identity
    auction_house: Mapped[str]
    sale_name: Mapped[str | None]
    sale_number: Mapped[str | None]
    lot_number: Mapped[str]
    auction_date: Mapped[date | None]
    
    # Coin data from listing
    title: Mapped[str | None]
    description: Mapped[str | None]
    category: Mapped[str | None]
    metal: Mapped[str | None]
    denomination: Mapped[str | None]
    ruler: Mapped[str | None]
    
    # Physical
    weight_g: Mapped[Decimal | None]
    diameter_mm: Mapped[Decimal | None]
    
    # Pricing
    estimate_low: Mapped[Decimal | None]
    estimate_high: Mapped[Decimal | None]
    hammer_price: Mapped[Decimal | None]
    total_price: Mapped[Decimal | None]  # With buyer premium
    currency: Mapped[str]
    
    # References
    reference_text: Mapped[str | None]  # Raw reference string
    
    # Source
    url: Mapped[str]
    image_urls: Mapped[list[str] | None]  # JSON array
    
    # Scraping metadata
    scraped_at: Mapped[datetime]
    scraper_version: Mapped[str | None]
```

### Audit Models

#### `audit_run.py`

Audit session tracking.

```python
class AuditRun(Base):
    __tablename__ = "audit_runs"
    
    id: Mapped[int]
    started_at: Mapped[datetime]
    completed_at: Mapped[datetime | None]
    
    # Scope
    coin_ids: Mapped[list[int] | None]  # JSON array, null = all
    
    # Results
    coins_audited: Mapped[int]
    discrepancies_found: Mapped[int]
    enrichments_suggested: Mapped[int]
    
    status: Mapped[str]  # running, completed, failed
    error_message: Mapped[str | None]
```

#### `discrepancy.py`

Data conflict records.

```python
class DiscrepancyRecord(Base):
    __tablename__ = "discrepancies"
    
    id: Mapped[int]
    audit_run_id: Mapped[int]
    coin_id: Mapped[int]
    auction_data_id: Mapped[int | None]
    
    field_name: Mapped[str]         # "weight_g", "denomination"
    coin_value: Mapped[str | None]  # Current value
    auction_value: Mapped[str | None]  # Suggested value
    
    difference_type: Mapped[str]    # measurement, grade, reference, text
    severity: Mapped[str]           # low, medium, high
    
    status: Mapped[str]             # pending, accepted, rejected, ignored
    resolution_note: Mapped[str | None]
    resolved_at: Mapped[datetime | None]
```

#### `enrichment.py`

Field enrichment suggestions.

```python
class EnrichmentRecord(Base):
    __tablename__ = "enrichments"
    
    id: Mapped[int]
    audit_run_id: Mapped[int | None]
    coin_id: Mapped[int]
    source_type: Mapped[str]  # catalog, auction, manual
    source_id: Mapped[str | None]
    
    field_name: Mapped[str]
    suggested_value: Mapped[str]
    confidence: Mapped[float]  # 0.0 - 1.0
    
    status: Mapped[str]  # pending, applied, rejected
    applied_at: Mapped[datetime | None]
```

#### `field_history.py`

Field change tracking for rollback.

```python
class FieldHistory(Base):
    __tablename__ = "field_history"
    
    id: Mapped[int]
    coin_id: Mapped[int]
    field_name: Mapped[str]
    
    old_value: Mapped[str | None]
    new_value: Mapped[str | None]
    
    source: Mapped[str]  # user, auto_merge, enrichment
    source_id: Mapped[str | None]
    
    changed_at: Mapped[datetime]
```

---

## Schemas (`app/schemas/`)

### `coin.py`

```python
# List item (minimal fields)
class CoinListItem(BaseModel):
    id: int
    category: Category
    metal: Metal | None
    denomination: str | None
    issuing_authority: str | None
    grade: str | None
    acquisition_price: Decimal | None
    primary_image_url: str | None

# Full detail
class CoinDetail(CoinListItem):
    # All Coin fields plus:
    mint: MintSchema | None
    references: list[CoinReferenceSchema]
    images: list[CoinImageSchema]
    provenance_events: list[ProvenanceEventSchema]
    tags: list[CoinTagSchema]
    countermarks: list[CountermarkSchema]
    auction_data: list[AuctionDataSchema]

# Create/Update
class CoinCreate(BaseModel):
    category: Category = Category.imperial
    # All editable fields...

class CoinUpdate(BaseModel):
    # All fields optional for partial updates
    category: Category | None = None
    ...

# Paginated response
class PaginatedCoins(BaseModel):
    items: list[CoinListItem]
    total: int
    page: int
    per_page: int
    pages: int
```

### `audit.py`

```python
class DiscrepancySchema(BaseModel):
    id: int
    coin_id: int
    field_name: str
    coin_value: str | None
    auction_value: str | None
    difference_type: str
    severity: str
    status: str

class EnrichmentSchema(BaseModel):
    id: int
    coin_id: int
    field_name: str
    suggested_value: str
    confidence: float
    source_type: str
    status: str

class AuditRunSchema(BaseModel):
    id: int
    started_at: datetime
    completed_at: datetime | None
    coins_audited: int
    discrepancies_found: int
    enrichments_suggested: int
    status: str
```

---

## Routers (`app/routers/`)

### `coins.py` - Core CRUD

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/coins` | List coins with filters/pagination |
| GET | `/api/coins/{id}` | Get coin detail |
| POST | `/api/coins` | Create new coin |
| PUT | `/api/coins/{id}` | Update coin |
| DELETE | `/api/coins/{id}` | Delete coin |
| GET | `/api/coins/{id}/nav` | Get prev/next IDs for navigation |

**Query Parameters for List:**
- `category`, `metal`, `rarity` - Enum filters
- `ruler` - Text search on issuing_authority
- `mint` - Mint name filter
- `grade_min`, `grade_max` - Grade range
- `year_start`, `year_end` - Date range
- `price_min`, `price_max` - Price range
- `search` - Full-text search
- `sort_by`, `sort_dir` - Sorting
- `page`, `per_page` - Pagination

### `import_export.py` - Import Operations

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/import/url` | Parse auction URL |
| POST | `/api/import/ngc` | NGC certificate lookup |
| POST | `/api/import/excel` | Excel/CSV import |
| POST | `/api/import/batch` | Batch import multiple coins |
| POST | `/api/import/preview` | Preview import without saving |
| POST | `/api/import/duplicates` | Check for duplicates |

### `audit.py` - Audit System

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/audit/start` | Start new audit run |
| GET | `/api/audit/runs` | List audit runs |
| GET | `/api/audit/runs/{id}` | Get audit run detail |
| GET | `/api/audit/summary` | Get audit summary stats |
| GET | `/api/audit/discrepancies` | List discrepancies |
| POST | `/api/audit/discrepancies/{id}/resolve` | Resolve discrepancy |
| GET | `/api/audit/enrichments` | List enrichments |
| POST | `/api/audit/enrichments/{id}/apply` | Apply enrichment |
| POST | `/api/audit/enrichments/{id}/reject` | Reject enrichment |
| POST | `/api/audit/auto-merge` | Run auto-merge |
| POST | `/api/audit/rollback/{id}` | Rollback field change |

### `catalog.py` - Reference Lookups

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/catalog/lookup` | Lookup reference in catalogs |
| POST | `/api/catalog/enrich/{coin_id}` | Enrich coin from catalogs |
| POST | `/api/catalog/bulk-enrich` | Bulk enrichment job |
| GET | `/api/catalog/jobs/{job_id}` | Get job status |

### `scrape.py` - Auction Scraping

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/scrape/url` | Scrape single URL |
| POST | `/api/scrape/batch` | Scrape multiple URLs |
| POST | `/api/scrape/browser` | Browser-based scrape |
| GET | `/api/scrape/jobs/{id}` | Get scrape job status |

### `auctions.py` - Auction Data

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/auctions` | List auction records |
| GET | `/api/auctions/{id}` | Get auction detail |
| POST | `/api/auctions` | Create auction record |
| DELETE | `/api/auctions/{id}` | Delete auction record |
| GET | `/api/auctions/comparables/{coin_id}` | Find comparable auctions |
| GET | `/api/auctions/stats` | Price statistics |

### `stats.py` - Statistics

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/stats` | Collection statistics |
| GET | `/api/stats/by-category` | Stats by category |
| GET | `/api/stats/by-metal` | Stats by metal |
| GET | `/api/stats/by-ruler` | Stats by ruler |
| GET | `/api/stats/price-distribution` | Price histogram |

---

## Services (`app/services/`)

### Catalog Services (`services/catalogs/`)

#### `base.py` - Abstract Base

```python
class CatalogService(ABC):
    @abstractmethod
    async def lookup(self, reference: str) -> CatalogResult | None:
        """Look up a reference in the catalog."""
        
    @abstractmethod
    async def search(self, query: str) -> list[CatalogResult]:
        """Search the catalog."""
```

#### `ocre.py` - OCRE Integration

Online Coins of the Roman Empire (Imperial coins).

- **Website:** http://numismatics.org/ocre/
- **Coverage:** Roman Imperial Coinage (RIC) - 27 BC to AD 491
- **Example lookup:** RIC I 207 → http://numismatics.org/ocre/id/ric.1(2).aug.207

```python
class OCREService(CatalogService):
    BASE_URL = "http://numismatics.org/ocre/"
    
    async def lookup(self, reference: str) -> CatalogResult | None:
        # Parses "RIC I 207" -> API call
        # Returns coin data, images, description
        
    async def get_coin_data(self, ric_id: str) -> dict:
        # Fetch full coin data from OCRE
```

#### `crro.py` - CRRO Integration

Coinage of the Roman Republic Online (Republican coins).

- **Website:** http://numismatics.org/crro/
- **Coverage:** Roman Republican coins (Crawford references)
- **Example lookup:** Crawford 44/5 → http://numismatics.org/crro/id/rrc-44.5

```python
class CRROService(CatalogService):
    BASE_URL = "http://numismatics.org/crro/"
    
    # Similar interface, handles Crawford references
```

#### `rpc.py` - RPC Integration

Roman Provincial Coinage.

- **Website:** https://rpc.ashmus.ox.ac.uk/
- **Coverage:** Roman Provincial coins (Greek Imperial)
- **Example lookup:** RPC I 1234 → https://rpc.ashmus.ox.ac.uk/coins/1/1234

```python
class RPCService(CatalogService):
    BASE_URL = "https://rpc.ashmus.ox.ac.uk/"
    
    # Handles RPC references
```

#### `registry.py` - Catalog Registry

```python
class CatalogRegistry:
    """Manages catalog service instances."""
    
    def get_service(self, system: str) -> CatalogService | None:
        """Get appropriate service for reference system."""
        # "RIC" -> OCREService
        # "Crawford" -> CRROService
        # "RPC" -> RPCService
```

### Scraper Services (`services/scrapers/`)

#### `base.py` - Scraper Base

```python
@dataclass
class LotData:
    """Extracted auction lot data."""
    auction_house: str
    sale_name: str | None
    lot_number: str
    title: str | None
    description: str | None
    category: str | None
    metal: str | None
    weight_g: Decimal | None
    diameter_mm: Decimal | None
    estimate_low: Decimal | None
    estimate_high: Decimal | None
    hammer_price: Decimal | None
    reference_text: str | None
    image_urls: list[str]
    url: str

class AuctionScraperBase(ABC):
    @abstractmethod
    async def scrape(self, url: str) -> LotData:
        """Scrape auction URL and return lot data."""
        
    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Check if scraper handles this URL."""
```

#### `orchestrator.py` - Scraper Orchestrator

```python
class AuctionOrchestrator:
    """Coordinates scraping across multiple auction sites."""
    
    scrapers: list[AuctionScraperBase]
    
    async def scrape(self, url: str) -> LotData:
        """Route URL to appropriate scraper."""
        for scraper in self.scrapers:
            if scraper.can_handle(url):
                return await scraper.scrape(url)
        raise UnsupportedURLError(url)
```

#### Individual Scrapers

| File | Target Site | URL |
|------|-------------|-----|
| `heritage.py` / `heritage_rich/` | Heritage Auctions | https://coins.ha.com |
| `cng.py` / `cng_rich/` | Classical Numismatic Group | https://cngcoins.com |
| `biddr.py` / `biddr_rich/` | Biddr/Savoca | https://biddr.com |
| `ebay.py` / `ebay_rich/` | eBay | https://www.ebay.com |
| `agora.py` | Agora Auctions | https://agoraauctions.com |
| `roma.py` | Roma Numismatics | https://romanumismatics.com |

#### `browser_scraper.py` - Playwright Scraper

```python
class BrowserScraper:
    """Playwright-based scraper for JavaScript-heavy sites."""
    
    async def scrape(self, url: str) -> str:
        """Load page with browser and return HTML."""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url)
            content = await page.content()
            await browser.close()
            return content
```

### Audit Services (`services/audit/`)

#### `audit_service.py` - Main Audit Service

```python
class AuditService:
    """Runs audits comparing coins to auction data."""
    
    async def run_audit(
        self, 
        db: Session, 
        coin_ids: list[int] | None = None
    ) -> AuditRun:
        """Run audit on specified coins or all coins."""
        # 1. Create AuditRun record
        # 2. For each coin, find linked auction data
        # 3. Compare fields using NumismaticComparator
        # 4. Create discrepancy records for differences
        # 5. Suggest enrichments for missing fields
        # 6. Return completed audit run
```

#### `auto_merge.py` - Auto-Merge Service

```python
class AutoMergeService:
    """Automatically merge high-confidence enrichments."""
    
    trust_config: TrustConfig
    
    async def auto_merge(
        self, 
        db: Session, 
        coin_id: int
    ) -> list[FieldHistory]:
        """Merge trusted enrichments into coin."""
        # 1. Get pending enrichments
        # 2. Check confidence against trust threshold
        # 3. Apply enrichments that meet threshold
        # 4. Record changes in FieldHistory
```

#### `trust_config.py` - Trust Configuration

```python
class TrustConfig:
    """Trust levels for different data sources."""
    
    # Source trust levels (0.0 - 1.0)
    CATALOG_TRUST = 0.9    # OCRE, CRRO, RPC
    AUCTION_TRUST = 0.7    # Auction house data
    LLM_TRUST = 0.5        # LLM suggestions
    
    # Field thresholds for auto-merge
    AUTO_MERGE_THRESHOLD = {
        "weight_g": 0.8,
        "diameter_mm": 0.8,
        "denomination": 0.85,
        "obverse_legend": 0.7,
        "reverse_legend": 0.7,
    }
```

#### `comparator.py` - Numismatic Comparator

```python
class NumismaticComparator:
    """Compares coin fields with numismatic awareness."""
    
    def compare(
        self, 
        coin: Coin, 
        auction: AuctionData
    ) -> list[FieldDifference]:
        """Compare coin to auction data."""
        # Handles:
        # - Weight tolerance (±0.05g)
        # - Diameter tolerance (±0.5mm)
        # - Text normalization for legends
        # - Reference format variations
```

### Import Services

#### `excel_import.py`

```python
class ExcelImporter:
    """Import coins from Excel/CSV files."""
    
    def parse_file(self, file: UploadFile) -> list[CoinCreate]:
        """Parse Excel/CSV to coin schemas."""
        
    def normalize_fields(self, row: dict) -> dict:
        """Normalize field names and values."""
```

#### `reference_parser.py`

```python
class ReferenceParser:
    """Parse catalog reference strings."""
    
    def parse(self, text: str) -> list[ParsedReference]:
        """Parse reference like 'RIC I 207' or 'Crawford 335/1'."""
        # Returns system, volume, number components
```

#### `ngc_connector.py`

```python
class NGCConnector:
    """NGC certification lookup."""
    
    async def lookup(self, cert_number: str) -> NGCCoinData | None:
        """Look up coin by NGC certification number."""
```

#### `legend_dictionary.py`

```python
class LegendDictionary:
    """Roman legend abbreviation expansion."""
    
    ABBREVIATIONS = {
        "IMP": "Imperator",
        "CAES": "Caesar",
        "AVG": "Augustus",
        "PM": "Pontifex Maximus",
        "TRP": "Tribunicia Potestate",
        "COS": "Consul",
        "PP": "Pater Patriae",
        "SC": "Senatus Consulto",
        # ... many more
    }
    
    def expand(self, legend: str) -> str:
        """Expand abbreviations in legend."""
```

---

## CRUD (`app/crud/`)

### `coin.py`

```python
def get_coin(db: Session, coin_id: int) -> Coin | None:
    """Get single coin by ID with relationships."""

def get_coins(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    filters: CoinFilters | None = None,
    sort_by: str = "created_at",
    sort_dir: str = "desc"
) -> tuple[list[Coin], int]:
    """Get paginated coins with filters."""

def create_coin(db: Session, coin: CoinCreate) -> Coin:
    """Create new coin."""

def update_coin(db: Session, coin_id: int, coin: CoinUpdate) -> Coin | None:
    """Update existing coin."""

def delete_coin(db: Session, coin_id: int) -> bool:
    """Delete coin by ID."""

def get_coin_ids_sorted(
    db: Session, 
    filters: CoinFilters | None = None,
    sort_by: str = "created_at",
    sort_dir: str = "desc"
) -> list[int]:
    """Get sorted coin IDs for navigation."""
```

### `auction.py`

```python
def get_auctions(
    db: Session,
    filters: AuctionFilters | None = None,
    skip: int = 0,
    limit: int = 20
) -> tuple[list[AuctionData], int]:
    """Get paginated auctions."""

def upsert_auction(db: Session, auction: AuctionCreate) -> AuctionData:
    """Insert or update auction record."""

def get_comparables(
    db: Session, 
    coin_id: int,
    limit: int = 10
) -> list[AuctionData]:
    """Find comparable auctions for a coin."""

def get_price_stats(db: Session, reference: str) -> PriceStats:
    """Get price statistics for a reference."""
```

### `audit.py`

```python
def create_audit_run(db: Session, audit: AuditRunCreate) -> AuditRun:
    """Create new audit run."""

def create_discrepancy(db: Session, disc: DiscrepancyCreate) -> DiscrepancyRecord:
    """Create discrepancy record."""

def get_discrepancies(
    db: Session,
    filters: DiscrepancyFilters | None = None
) -> list[DiscrepancyRecord]:
    """Get discrepancies with filters."""

def resolve_discrepancy(
    db: Session,
    disc_id: int,
    status: str,
    note: str | None = None
) -> DiscrepancyRecord:
    """Resolve a discrepancy."""

def create_enrichment(db: Session, enr: EnrichmentCreate) -> EnrichmentRecord:
    """Create enrichment suggestion."""

def apply_enrichment(db: Session, enr_id: int) -> EnrichmentRecord:
    """Apply enrichment to coin."""
```

---

**Previous:** [02-ARCHITECTURE.md](02-ARCHITECTURE.md) - System architecture  
**Next:** [04-FRONTEND-MODULES.md](04-FRONTEND-MODULES.md) - Frontend module reference
