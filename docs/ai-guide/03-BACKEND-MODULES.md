# Backend Modules Reference (V2 Clean Architecture)

## Directory Structure

```
backend/src/
├── domain/                    # Domain Layer (no dependencies)
│   ├── coin.py                # Coin entity + value objects + enums
│   ├── auction.py             # AuctionLot entity
│   ├── series.py              # Series entity
│   ├── vocab.py               # VocabTerm entity
│   ├── repositories.py        # Repository interfaces (Protocols)
│   ├── services/              # Domain services
│   │   ├── audit_engine.py
│   │   ├── search_service.py
│   │   └── scraper_orchestrator.py
│   └── strategies/            # Audit strategies
│       ├── attribution_strategy.py
│       ├── physics_strategy.py
│       ├── date_strategy.py
│       └── grade_strategy.py
│
├── application/               # Application Layer (use cases)
│   └── commands/
│       ├── create_coin.py
│       ├── enrich_coin.py
│       ├── import_collection.py
│       └── scrape_auction_lot.py
│
└── infrastructure/            # Infrastructure Layer (external concerns)
    ├── persistence/           # Database & ORM
    │   ├── database.py        # SQLAlchemy setup
    │   ├── orm.py             # Core ORM models
    │   ├── models_vocab.py    # Vocabulary ORM models
    │   ├── models_series.py   # Series ORM models
    │   └── repositories/      # Concrete repository implementations
    │       ├── coin_repository.py
    │       ├── auction_data_repository.py
    │       ├── vocab_repository.py
    │       └── series_repository.py
    │
    ├── scrapers/              # Auction scrapers
    │   ├── base_playwright.py
    │   ├── heritage/
    │   ├── cng/
    │   ├── biddr/
    │   ├── ebay/
    │   └── agora/
    │
    ├── services/              # Infrastructure services
    │   ├── vocab_sync.py
    │   ├── series_service.py
    │   └── llm_service.py
    │
    ├── scripts/               # Maintenance scripts
    │   ├── add_indexes.py
    │   ├── migrate_v1_to_v2_data.py
    │   └── fix_category_mapping.py
    │
    └── web/                   # Web layer (FastAPI)
        ├── main.py            # FastAPI app
        ├── dependencies.py    # Dependency injection
        └── routers/
            ├── v2.py          # Coin CRUD
            ├── vocab.py       # Vocabulary management
            ├── series.py      # Series management
            ├── scrape_v2.py   # Scraping endpoints
            ├── audit_v2.py    # Audit endpoints (planned)
            ├── llm.py         # AI enrichment
            ├── provenance.py  # Provenance (planned)
            └── die_study.py   # Die study (planned)
```

---

## Domain Layer (`src/domain/`)

### Core Philosophy

**Domain layer has ZERO dependencies.** It contains pure business logic, entities, and interfaces. No SQLAlchemy, FastAPI, or Pydantic imports.

### `coin.py` - Coin Entity

**Coin** is the aggregate root with all numismatic fields.

```python
@dataclass
class Coin:
    """Aggregate root for coin entity."""

    # Identity
    id: Optional[int]

    # Classification (REQUIRED)
    category: str          # republic, imperial, provincial, byzantine, greek
    denomination: str      # Denarius, Aureus, Antoninianus
    metal: str            # gold, silver, bronze, billon

    # Attribution (WHO issued)
    issuing_authority: Optional[str]
    portrait_subject: Optional[str]
    dynasty: Optional[str]
    status: Optional[str]

    # Chronology (WHEN minted)
    reign_start: Optional[int]     # Negative for BC
    reign_end: Optional[int]
    mint_year_start: Optional[int]
    mint_year_end: Optional[int]

    # Geography (WHERE minted)
    mint: Optional[str]

    # Physical characteristics
    weight_g: Optional[Decimal]
    diameter_mm: Optional[Decimal]
    die_axis: Optional[int]        # 0-12 clock positions

    # Design & iconography
    obverse_legend: Optional[str]
    obverse_description: Optional[str]
    reverse_legend: Optional[str]
    reverse_description: Optional[str]
    exergue: Optional[str]

    # Grading
    grade_service: Optional[str]   # ngc, pcgs, self, dealer
    grade: Optional[str]
    certification_number: Optional[str]

    # Acquisition
    acquisition_date: Optional[date]
    acquisition_price: Optional[Decimal]
    acquisition_source: Optional[str]
    acquisition_url: Optional[str]

    # Storage & organization
    holder_type: Optional[str]
    storage_location: Optional[str]

    # Research
    rarity: Optional[str]
    historical_significance: Optional[str]
    personal_notes: Optional[str]

    # Collections
    images: List['CoinImage'] = field(default_factory=list)
    references: List['CoinReference'] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    # Value Objects
    dimensions: Optional['Dimensions'] = None
    attribution: Optional['Attribution'] = None
    grading_details: Optional['GradingDetails'] = None
    acquisition_details: Optional['AcquisitionDetails'] = None
```

**Value Objects** (immutable):
```python
@dataclass(frozen=True)
class Dimensions:
    weight_g: Optional[Decimal]
    diameter_mm: Optional[Decimal]
    die_axis: Optional[int]

@dataclass(frozen=True)
class Attribution:
    issuing_authority: Optional[str]
    portrait_subject: Optional[str]
    dynasty: Optional[str]
    status: Optional[str]

@dataclass(frozen=True)
class GradingDetails:
    service: str
    grade: str
    certification_number: Optional[str]

@dataclass(frozen=True)
class AcquisitionDetails:
    date: Optional[date]
    price: Optional[Decimal]
    source: Optional[str]
    url: Optional[str]
```

**Enums**:
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

class Metal(str, Enum):
    GOLD = "gold"
    SILVER = "silver"
    BILLON = "billon"
    BRONZE = "bronze"
    ELECTRUM = "electrum"
    ORICHALCUM = "orichalcum"
    POTIN = "potin"
    LEAD = "lead"
    AE = "ae"

class Rarity(str, Enum):
    COMMON = "common"
    SCARCE = "scarce"
    RARE = "rare"
    VERY_RARE = "very_rare"
    EXTREMELY_RARE = "extremely_rare"
    UNIQUE = "unique"

class GradeService(str, Enum):
    NGC = "ngc"
    PCGS = "pcgs"
    SELF = "self"
    DEALER = "dealer"
```

### `auction.py` - AuctionLot Entity

```python
@dataclass
class AuctionLot:
    """Auction lot data from scrapers."""

    # Identity
    url: str  # Unique identifier

    # Auction metadata
    auction_house: str
    lot_number: Optional[str]
    sale_name: Optional[str]
    sale_date: Optional[date]

    # Coin classification (mirrors Coin entity)
    category: Optional[str]
    denomination: Optional[str]
    metal: Optional[str]
    issuing_authority: Optional[str]
    portrait_subject: Optional[str]
    mint_year_start: Optional[int]
    mint_year_end: Optional[int]

    # Physical
    weight_g: Optional[Decimal]
    diameter_mm: Optional[Decimal]

    # Design
    obverse_description: Optional[str]
    reverse_description: Optional[str]

    # Grading & price
    grade: Optional[str]
    price_realized: Optional[Decimal]
    estimate_min: Optional[Decimal]
    estimate_max: Optional[Decimal]

    # References & images
    references: List[str] = field(default_factory=list)
    image_urls: List[str] = field(default_factory=list)

    # Full description
    description: Optional[str]
    provenance: Optional[str]
```

### `series.py` - Series Entity

```python
@dataclass
class Series:
    """Collection series/grouping."""

    id: Optional[int]
    slug: str  # URL-friendly unique identifier
    name: str
    category: str
    description: Optional[str]
    historical_context: Optional[str]
    coin_count: int = 0
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
```

### `vocab.py` - VocabTerm Entity

```python
@dataclass
class VocabTerm:
    """Controlled vocabulary term."""

    id: Optional[int]
    term_type: str  # "issuer", "mint", "ruler"
    canonical_name: str
    display_name: Optional[str]
    variants: List[str] = field(default_factory=list)
    category: Optional[str]
    start_year: Optional[int]
    end_year: Optional[int]
    coin_count: int = 0
```

### `repositories.py` - Repository Interfaces

**Protocols define repository interfaces (no implementation):**

```python
from typing import Protocol, Optional, List

class ICoinRepository(Protocol):
    """Repository interface for coins."""

    def get_by_id(self, coin_id: int) -> Optional[Coin]:
        ...

    def save(self, coin: Coin) -> Coin:
        ...

    def delete(self, coin_id: int) -> None:
        ...

    def get_all(self, skip: int = 0, limit: int = 100, **filters) -> List[Coin]:
        ...

    def count(self, **filters) -> int:
        ...

class IAuctionDataRepository(Protocol):
    """Repository interface for auction data."""

    def get_by_url(self, url: str) -> Optional[AuctionLot]:
        ...

    def save(self, lot: AuctionLot) -> AuctionLot:
        ...

    def get_comparables(self, coin_id: int, limit: int = 10) -> List[AuctionLot]:
        ...

class ISeriesRepository(Protocol):
    """Repository interface for series."""

    def get_by_slug(self, slug: str) -> Optional[Series]:
        ...

    def save(self, series: Series) -> Series:
        ...

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Series]:
        ...

class IVocabRepository(Protocol):
    """Repository interface for vocabulary."""

    def get_by_canonical_name(self, name: str, term_type: str) -> Optional[VocabTerm]:
        ...

    def save(self, term: VocabTerm) -> VocabTerm:
        ...

    def search(self, query: str, term_type: str, limit: int = 10) -> List[VocabTerm]:
        ...
```

### `services/` - Domain Services

#### `audit_engine.py`

```python
class AuditEngine:
    """Compares coin against reference data using strategies."""

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

#### `scraper_orchestrator.py`

```python
class ScraperOrchestrator:
    """Coordinates auction house scrapers."""

    def __init__(self, scrapers: List[IScraper]):
        self.scrapers = scrapers

    async def scrape(self, url: str) -> AuctionLot:
        """Route URL to appropriate scraper."""
        for scraper in self.scrapers:
            if scraper.can_handle(url):
                return await scraper.scrape(url)
        raise UnsupportedURLError(f"No scraper for: {url}")
```

### `strategies/` - Audit Strategies

Strategy pattern for pluggable audit checks:

```python
# attribution_strategy.py
class AttributionStrategy(AuditStrategy):
    """Check issuing authority and portrait subject."""

    def check(self, coin: Coin, reference: AuctionLot) -> AuditResult:
        if coin.issuing_authority != reference.issuing_authority:
            return AuditResult(
                field="issuing_authority",
                status="yellow",
                message=f"Mismatch: {coin.issuing_authority} vs {reference.issuing_authority}"
            )
        return AuditResult(field="issuing_authority", status="green")

# physics_strategy.py
class PhysicsStrategy(AuditStrategy):
    """Check weight and diameter within tolerances."""

    WEIGHT_TOLERANCE = Decimal("0.05")  # ±0.05g
    DIAMETER_TOLERANCE = Decimal("0.5")  # ±0.5mm

    def check(self, coin: Coin, reference: AuctionLot) -> AuditResult:
        if coin.weight_g and reference.weight_g:
            diff = abs(coin.weight_g - reference.weight_g)
            if diff > self.WEIGHT_TOLERANCE:
                return AuditResult(
                    field="weight_g",
                    status="red",
                    message=f"Weight difference: {diff}g"
                )
        return AuditResult(field="weight_g", status="green")
```

---

## Application Layer (`src/application/commands/`)

### Use Cases

Use cases orchestrate domain entities and services to fulfill application-specific business rules.

#### `create_coin.py`

```python
@dataclass
class CreateCoinDTO:
    """Input DTO for use case."""
    category: str
    denomination: str
    metal: str
    weight_g: Optional[float]
    # ... all coin fields

class CreateCoinUseCase:
    """Use case: Create new coin in collection."""

    def __init__(self, coin_repo: ICoinRepository):
        self.coin_repo = coin_repo  # Interface, not implementation

    def execute(self, dto: CreateCoinDTO) -> Coin:
        # Build domain entity
        coin = Coin(
            id=None,
            category=dto.category,
            denomination=dto.denomination,
            metal=dto.metal,
            weight_g=Decimal(dto.weight_g) if dto.weight_g else None,
            # ... map DTO to entity
        )

        # Domain validation
        errors = coin.validate()
        if errors:
            raise ValidationError(errors)

        # Save via repository
        return self.coin_repo.save(coin)
```

#### `enrich_coin.py`

```python
class EnrichCoinUseCase:
    """Use case: Enrich coin with external data."""

    def __init__(
        self,
        coin_repo: ICoinRepository,
        auction_repo: IAuctionDataRepository
    ):
        self.coin_repo = coin_repo
        self.auction_repo = auction_repo

    def execute(self, coin_id: int) -> Coin:
        # Get coin
        coin = self.coin_repo.get_by_id(coin_id)
        if not coin:
            raise CoinNotFoundError(coin_id)

        # Find comparable auction data
        comparables = self.auction_repo.get_comparables(coin_id)

        # Enrich missing fields from comparables
        for comparable in comparables:
            if not coin.weight_g and comparable.weight_g:
                coin.weight_g = comparable.weight_g
            if not coin.diameter_mm and comparable.diameter_mm:
                coin.diameter_mm = comparable.diameter_mm

        # Save enriched coin
        return self.coin_repo.save(coin)
```

---

## Infrastructure Layer (`src/infrastructure/`)

### Persistence (`src/infrastructure/persistence/`)

#### `database.py` - SQLAlchemy Setup

```python
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

SQLALCHEMY_DATABASE_URL = "sqlite:///./backend/coinstack_v2.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)

# Enable foreign key constraints
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)
```

#### `orm.py` - Core ORM Models

**IMPORTANT**: ORM models are separate from domain entities.

```python
from sqlalchemy import Integer, String, Numeric, Date, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List
from decimal import Decimal
from datetime import date

class CoinModel(Base):
    """ORM model for coins (separate from domain entity)."""
    __tablename__ = "coins_v2"

    # Use SQLAlchemy 2.0 Mapped[T] syntax
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category: Mapped[str] = mapped_column(String, index=True)
    denomination: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    metal: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)

    issuing_authority: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    portrait_subject: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    weight_g: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    diameter_mm: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    die_axis: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships with eager loading
    images: Mapped[List["CoinImageModel"]] = relationship(
        back_populates="coin",
        cascade="all, delete-orphan"
    )

    auction_data: Mapped[List["AuctionDataModel"]] = relationship(
        back_populates="coin"
    )

class CoinImageModel(Base):
    """ORM model for coin images."""
    __tablename__ = "coin_images_v2"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    coin_id: Mapped[int] = mapped_column(Integer, ForeignKey("coins_v2.id"))
    image_type: Mapped[str] = mapped_column(String)
    file_path: Mapped[str] = mapped_column(String)
    perceptual_hash: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    coin: Mapped["CoinModel"] = relationship(back_populates="images")
```

#### `models_vocab.py` - Vocabulary ORM Models

```python
class IssuerModel(Base):
    """ORM model for issuing authorities."""
    __tablename__ = "issuers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    canonical_name: Mapped[str] = mapped_column(String, unique=True, index=True)
    display_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    variants: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    category: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    start_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    end_year: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    coin_count: Mapped[int] = mapped_column(Integer, default=0)

class MintModel(Base):
    """ORM model for mint locations."""
    __tablename__ = "mints"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    canonical_name: Mapped[str] = mapped_column(String, unique=True, index=True)
    display_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    region: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    coin_count: Mapped[int] = mapped_column(Integer, default=0)
```

#### `repositories/coin_repository.py` - Concrete Repository

```python
from sqlalchemy.orm import Session, selectinload
from src.domain.coin import Coin
from src.domain.repositories import ICoinRepository
from src.infrastructure.persistence.orm import CoinModel

class SqlAlchemyCoinRepository:
    """Concrete implementation of ICoinRepository."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, coin_id: int) -> Optional[Coin]:
        # CRITICAL: Use selectinload() to prevent N+1 queries
        orm_coin = self.session.query(CoinModel).options(
            selectinload(CoinModel.images),
            selectinload(CoinModel.auction_data)
        ).filter(CoinModel.id == coin_id).first()

        return self._to_domain(orm_coin) if orm_coin else None

    def save(self, coin: Coin) -> Coin:
        orm_coin = self._to_orm(coin)
        merged = self.session.merge(orm_coin)
        self.session.flush()  # Get ID, but DON'T commit
        return self._to_domain(merged)

    def get_all(self, skip: int = 0, limit: int = 100, **filters) -> List[Coin]:
        query = self.session.query(CoinModel).options(
            selectinload(CoinModel.images)
        )

        # Apply filters
        if filters.get('category'):
            query = query.filter(CoinModel.category == filters['category'])
        if filters.get('metal'):
            query = query.filter(CoinModel.metal == filters['metal'])

        orm_coins = query.offset(skip).limit(limit).all()
        return [self._to_domain(c) for c in orm_coins]

    def _to_domain(self, orm_coin: CoinModel) -> Coin:
        """Convert ORM model to domain entity."""
        return Coin(
            id=orm_coin.id,
            category=orm_coin.category,
            denomination=orm_coin.denomination,
            metal=orm_coin.metal,
            weight_g=orm_coin.weight_g,
            # ... map all fields
        )

    def _to_orm(self, coin: Coin) -> CoinModel:
        """Convert domain entity to ORM model."""
        return CoinModel(
            id=coin.id,
            category=coin.category,
            denomination=coin.denomination,
            metal=coin.metal,
            weight_g=coin.weight_g,
            # ... map all fields
        )
```

### Web Layer (`src/infrastructure/web/`)

#### `main.py` - FastAPI App

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.infrastructure.web.routers import v2, vocab, series, scrape_v2

app = FastAPI(title="CoinStack API", version="2.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(v2.router, prefix="/api/v2", tags=["coins"])
app.include_router(vocab.router, prefix="/api/v2", tags=["vocab"])
app.include_router(series.router, prefix="/api/v2", tags=["series"])
app.include_router(scrape_v2.router, prefix="/api/v2", tags=["scrape"])
```

#### `dependencies.py` - Dependency Injection

```python
from sqlalchemy.orm import Session
from typing import Generator
from src.domain.repositories import ICoinRepository
from src.infrastructure.persistence.database import SessionLocal
from src.infrastructure.repositories.coin_repository import SqlAlchemyCoinRepository

def get_db() -> Generator[Session, None, None]:
    """Provides SQLAlchemy session with automatic transaction management."""
    db = SessionLocal()
    try:
        yield db
        db.commit()  # Auto-commit on success
    except Exception:
        db.rollback()  # Auto-rollback on error
        raise
    finally:
        db.close()

def get_coin_repository(db: Session = Depends(get_db)) -> ICoinRepository:
    """Provides concrete repository implementation."""
    return SqlAlchemyCoinRepository(db)
```

#### `routers/v2.py` - Coin CRUD Endpoints

```python
from fastapi import APIRouter, Depends, HTTPException
from src.application.commands.create_coin import CreateCoinUseCase, CreateCoinDTO
from src.domain.repositories import ICoinRepository
from src.infrastructure.web.dependencies import get_coin_repository

router = APIRouter()

@router.post("/coins", response_model=CoinSchema)
def create_coin(
    dto: CreateCoinDTO,
    coin_repo: ICoinRepository = Depends(get_coin_repository)
):
    """Create new coin (thin adapter to use case)."""
    use_case = CreateCoinUseCase(coin_repo)
    coin = use_case.execute(dto)
    return coin

@router.get("/coins/{coin_id}", response_model=CoinSchema)
def get_coin(
    coin_id: int,
    coin_repo: ICoinRepository = Depends(get_coin_repository)
):
    """Get single coin by ID."""
    coin = coin_repo.get_by_id(coin_id)
    if not coin:
        raise HTTPException(status_code=404, detail="Coin not found")
    return coin

@router.get("/coins", response_model=PaginatedCoinsSchema)
def list_coins(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    metal: Optional[str] = None,
    coin_repo: ICoinRepository = Depends(get_coin_repository)
):
    """List coins with filters."""
    filters = {}
    if category:
        filters['category'] = category
    if metal:
        filters['metal'] = metal

    coins = coin_repo.get_all(skip=skip, limit=limit, **filters)
    total = coin_repo.count(**filters)

    return {
        "items": coins,
        "total": total,
        "skip": skip,
        "limit": limit
    }
```

### Scrapers (`src/infrastructure/scrapers/`)

#### `base_playwright.py`

```python
from abc import ABC, abstractmethod
from playwright.async_api import async_playwright

class BaseScraper(ABC):
    """Base class for Playwright-based scrapers."""

    @abstractmethod
    def can_handle(self, url: str) -> bool:
        """Check if scraper handles this URL."""
        pass

    @abstractmethod
    async def scrape(self, url: str) -> AuctionLot:
        """Scrape auction lot from URL."""
        pass

    async def _fetch_html(self, url: str) -> str:
        """Fetch HTML with Playwright."""
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            await page.goto(url)
            content = await page.content()
            await browser.close()
            return content
```

#### `heritage/scraper.py`

```python
class HeritageScraper(BaseScraper):
    """Rich scraper for Heritage Auctions."""

    def can_handle(self, url: str) -> bool:
        return "coins.ha.com" in url

    async def scrape(self, url: str) -> AuctionLot:
        html = await self._fetch_html(url)
        parser = HeritageParser(html)

        return AuctionLot(
            url=url,
            auction_house="Heritage",
            lot_number=parser.get_lot_number(),
            category=parser.get_category(),
            denomination=parser.get_denomination(),
            issuing_authority=parser.get_issuer(),
            price_realized=parser.get_price(),
            image_urls=parser.get_images(),
            # ... extract all fields
        )
```

---

## Key Patterns & Best Practices

### 1. Clean Architecture Dependency Rule

```python
# ✅ CORRECT - Domain depends on nothing
from dataclasses import dataclass
from typing import Optional

@dataclass
class Coin:
    id: Optional[int]
    category: str

# ❌ WRONG - Domain depending on SQLAlchemy
from sqlalchemy.orm import Mapped
from src.infrastructure.persistence.orm import CoinModel

class Coin(CoinModel):  # NO!
    pass
```

### 2. Repository Pattern

```python
# ✅ CORRECT - Use case depends on interface
class CreateCoinUseCase:
    def __init__(self, repo: ICoinRepository):  # Protocol
        self.repo = repo

# ❌ WRONG - Use case depends on concrete class
class CreateCoinUseCase:
    def __init__(self, repo: SqlAlchemyCoinRepository):  # Concrete
        self.repo = repo
```

### 3. Transaction Management

```python
# ✅ CORRECT - Repository uses flush(), not commit()
def save(self, coin: Coin) -> Coin:
    orm_coin = self._to_orm(coin)
    merged = self.session.merge(orm_coin)
    self.session.flush()  # Get ID
    return self._to_domain(merged)

# ❌ WRONG - Repository commits transaction
def save(self, coin: Coin) -> Coin:
    orm_coin = self._to_orm(coin)
    self.session.add(orm_coin)
    self.session.commit()  # NO! Breaks transaction boundaries
    return self._to_domain(orm_coin)
```

### 4. N+1 Query Prevention

```python
# ✅ CORRECT - Eager loading with selectinload()
from sqlalchemy.orm import selectinload

orm_coin = self.session.query(CoinModel).options(
    selectinload(CoinModel.images)  # 1 extra query for all images
).filter(CoinModel.id == coin_id).first()

# ❌ WRONG - Lazy loading causes N+1 queries
orm_coin = self.session.query(CoinModel).filter(
    CoinModel.id == coin_id
).first()  # 1 query + N queries for images
```

---

**Previous:** [02-CLEAN-ARCHITECTURE.md](02-CLEAN-ARCHITECTURE.md) - Clean Architecture principles
**Next:** [04-DOMAIN-ENTITIES.md](04-DOMAIN-ENTITIES.md) - Domain entities and value objects
