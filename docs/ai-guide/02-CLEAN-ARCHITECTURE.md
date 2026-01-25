# Clean Architecture (V2)

## Architecture Overview

CoinStack V2 follows **Clean Architecture** principles with strict dependency rules and clear separation of concerns across three layers.

### The Dependency Rule

**Dependencies flow INWARD only:**

```
Infrastructure Layer
    ↓ depends on
Application Layer
    ↓ depends on
Domain Layer (no dependencies)
```

**Critical Principle**: Domain layer has ZERO dependencies. It doesn't know about FastAPI, SQLAlchemy, databases, or web frameworks.

## Layer Responsibilities

### Domain Layer (`src/domain/`)

**Purpose**: Pure business logic, entities, value objects, and domain services.

**Contains**:
- **Entities**: `Coin`, `AuctionLot`, `Series`, `VocabTerm`
- **Value Objects**: `Dimensions`, `Attribution`, `GradingDetails`, `AcquisitionDetails`
- **Domain Services**: `AuditEngine`, `ScraperOrchestrator`, `SearchService`
- **Strategies**: `AttributionStrategy`, `PhysicsStrategy`, `DateStrategy`, `GradeStrategy`
- **Repository Interfaces** (Protocols): `ICoinRepository`, `IAuctionDataRepository`, `ISeriesRepository`, `IVocabRepository`
- **Enums**: `Category`, `Metal`, `Rarity`, `GradeService`

**Rules**:
- NO external dependencies (no SQLAlchemy, FastAPI, Pydantic)
- Only standard library imports (typing, dataclasses, enum, datetime, Decimal)
- Domain logic is framework-agnostic
- Uses Protocol for interface definitions

**Example - Domain Entity**:
```python
# src/domain/coin.py
from dataclasses import dataclass
from typing import Optional, List
from decimal import Decimal
from datetime import date

@dataclass
class Coin:
    """Coin aggregate root - central domain entity."""
    id: Optional[int]
    category: str
    denomination: str
    metal: str
    weight_g: Optional[Decimal]
    diameter_mm: Optional[Decimal]
    die_axis: Optional[int]

    # Value Objects
    dimensions: Optional['Dimensions']
    attribution: Optional['Attribution']
    grading: Optional['GradingDetails']
    acquisition: Optional['AcquisitionDetails']

    # Collections
    images: List['CoinImage']
    references: List['CoinReference']
```

**Example - Repository Interface**:
```python
# src/domain/repositories.py
from typing import Protocol, Optional, List

class ICoinRepository(Protocol):
    """Repository interface - no implementation details."""

    def get_by_id(self, coin_id: int) -> Optional[Coin]:
        ...

    def save(self, coin: Coin) -> Coin:
        ...

    def delete(self, coin_id: int) -> None:
        ...

    def get_all(self, skip: int = 0, limit: int = 100, **filters) -> List[Coin]:
        ...
```

### Application Layer (`src/application/`)

**Purpose**: Use cases (application-specific business rules).

**Contains**:
- **Commands**: `CreateCoinUseCase`, `EnrichCoinUseCase`, `ImportCollectionUseCase`, `ScrapeAuctionLotUseCase`
- **DTOs**: Data Transfer Objects for use case inputs/outputs

**Rules**:
- Depends on Domain layer only (entities, repositories, domain services)
- NO direct dependency on Infrastructure (no SQLAlchemy, no FastAPI)
- Orchestrates domain entities and services
- Uses repository interfaces, not implementations

**Example - Use Case**:
```python
# src/application/commands/create_coin.py
from dataclasses import dataclass
from src.domain.coin import Coin
from src.domain.repositories import ICoinRepository

@dataclass
class CreateCoinDTO:
    """Input DTO for use case."""
    category: str
    denomination: str
    metal: str
    weight_g: Optional[float]
    # ... other fields

class CreateCoinUseCase:
    """Application use case - orchestrates domain logic."""

    def __init__(self, coin_repo: ICoinRepository):
        self.coin_repo = coin_repo  # Interface, not implementation

    def execute(self, dto: CreateCoinDTO) -> Coin:
        # Create domain entity
        coin = Coin(
            id=None,
            category=dto.category,
            denomination=dto.denomination,
            metal=dto.metal,
            # ... map DTO to entity
        )

        # Domain validation (could be in entity)
        if coin.weight_g and coin.weight_g <= 0:
            raise ValueError("Weight must be positive")

        # Save via repository interface
        return self.coin_repo.save(coin)
```

### Infrastructure Layer (`src/infrastructure/`)

**Purpose**: External concerns - databases, web frameworks, scrapers, file I/O.

**Contains**:
- **Persistence** (`persistence/`):
  - ORM Models: `CoinModel`, `IssuerModel`, `SeriesModel`
  - Concrete Repositories: `SqlAlchemyCoinRepository`, `SqlAlchemyVocabRepository`
  - Database setup: `database.py`, `orm.py`
- **Web** (`web/`):
  - FastAPI app: `main.py`
  - Routers: `v2.py`, `vocab.py`, `series.py`, `scrape_v2.py`, `audit_v2.py`
  - Dependencies: `dependencies.py`
- **Scrapers** (`scrapers/`):
  - Implementations: `HeritageScraper`, `CNGScraper`, `BiddrScraper`, `EBayScraper`
- **Services** (`services/`):
  - Infrastructure services: `VocabSyncService`, `SeriesService`, `LLMService`

**Rules**:
- Implements repository interfaces from Domain
- Translates between domain entities and ORM models
- Handles framework-specific details (FastAPI, SQLAlchemy)
- Depends on both Domain and Application layers

**Example - Concrete Repository**:
```python
# src/infrastructure/repositories/coin_repository.py
from sqlalchemy.orm import Session, selectinload
from src.domain.coin import Coin
from src.domain.repositories import ICoinRepository
from src.infrastructure.persistence.orm import CoinModel

class SqlAlchemyCoinRepository:
    """Concrete implementation of repository interface."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, coin_id: int) -> Optional[Coin]:
        # Query ORM model with eager loading
        orm_coin = self.session.query(CoinModel).options(
            selectinload(CoinModel.images)
        ).filter(CoinModel.id == coin_id).first()

        # Convert to domain entity
        return self._to_domain(orm_coin) if orm_coin else None

    def save(self, coin: Coin) -> Coin:
        # Convert domain entity to ORM model
        orm_coin = self._to_orm(coin)

        # Persist
        merged = self.session.merge(orm_coin)
        self.session.flush()  # Get ID, but don't commit

        # Convert back to domain
        return self._to_domain(merged)

    def _to_domain(self, orm_coin: CoinModel) -> Coin:
        """ORM → Domain entity."""
        return Coin(
            id=orm_coin.id,
            category=orm_coin.category,
            # ... map all fields
        )

    def _to_orm(self, coin: Coin) -> CoinModel:
        """Domain entity → ORM."""
        return CoinModel(
            id=coin.id,
            category=coin.category,
            # ... map all fields
        )
```

**Example - Web Router**:
```python
# src/infrastructure/web/routers/v2.py
from fastapi import APIRouter, Depends
from src.application.commands.create_coin import CreateCoinUseCase, CreateCoinDTO
from src.domain.repositories import ICoinRepository
from src.infrastructure.web.dependencies import get_coin_repository

router = APIRouter(prefix="/api/v2", tags=["coins"])

@router.post("/coins")
def create_coin(
    dto: CreateCoinDTO,
    coin_repo: ICoinRepository = Depends(get_coin_repository)
):
    """Web endpoint - thin adapter to use case."""
    use_case = CreateCoinUseCase(coin_repo)
    coin = use_case.execute(dto)
    return coin  # Auto-serialized by FastAPI
```

## Dependency Injection Flow

**How layers connect at runtime:**

1. **FastAPI Dependency** (`dependencies.py`):
```python
# src/infrastructure/web/dependencies.py
from sqlalchemy.orm import Session
from src.domain.repositories import ICoinRepository
from src.infrastructure.repositories.coin_repository import SqlAlchemyCoinRepository

def get_db() -> Generator[Session, None, None]:
    """Provides SQLAlchemy session with transaction management."""
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
    """Returns concrete repository implementation."""
    return SqlAlchemyCoinRepository(db)
```

2. **Router** injects repository into use case:
```python
@router.post("/coins")
def create_coin(
    dto: CreateCoinDTO,
    coin_repo: ICoinRepository = Depends(get_coin_repository)  # Injected
):
    use_case = CreateCoinUseCase(coin_repo)  # Use case gets interface
    return use_case.execute(dto)
```

3. **Use Case** calls repository via interface:
```python
class CreateCoinUseCase:
    def __init__(self, coin_repo: ICoinRepository):
        self.coin_repo = coin_repo  # Interface, not SqlAlchemyCoinRepository

    def execute(self, dto: CreateCoinDTO) -> Coin:
        coin = self._build_coin(dto)
        return self.coin_repo.save(coin)  # Polymorphic call
```

## Benefits of This Architecture

### 1. Testability
- **Unit tests**: Test domain entities and use cases with mock repositories (no database)
- **Integration tests**: Test real repositories with test database
- **Fast tests**: Domain layer tests run in milliseconds

### 2. Maintainability
- **Clear boundaries**: Each layer has single responsibility
- **Easy to locate logic**: Domain logic in domain/, persistence in infrastructure/
- **No shotgun surgery**: Change database → only touch infrastructure/

### 3. Flexibility
- **Swap implementations**: Replace SQLite with Postgres → only change infrastructure/
- **Framework independence**: Migrate from FastAPI to Django → only change infrastructure/web/
- **Multiple UIs**: Could add CLI, desktop app, mobile app using same domain/application

### 4. Domain Focus
- **Business logic first**: Domain entities encode numismatic rules
- **Framework agnostic**: Domain code doesn't care about web frameworks or databases
- **Expert knowledge preserved**: Coin grading, auction data, catalog references in domain

## Anti-Patterns to Avoid

### ❌ Domain Depending on Infrastructure
```python
# src/domain/coin.py - WRONG
from sqlalchemy import Column, Integer, String  # ❌ SQLAlchemy in domain
from src.infrastructure.persistence.orm import CoinModel  # ❌ Infrastructure in domain

class Coin(CoinModel):  # ❌ Domain entity inheriting from ORM
    pass
```

### ❌ Use Cases Depending on ORM
```python
# src/application/commands/create_coin.py - WRONG
from sqlalchemy.orm import Session  # ❌ SQLAlchemy in application
from src.infrastructure.persistence.orm import CoinModel  # ❌ ORM in application

class CreateCoinUseCase:
    def __init__(self, db: Session):  # ❌ Concrete session, not interface
        self.db = db

    def execute(self, dto: CreateCoinDTO) -> Coin:
        orm_coin = CoinModel(...)  # ❌ Creating ORM model in use case
        self.db.add(orm_coin)
        self.db.commit()  # ❌ Committing in use case
```

### ❌ Routers with Business Logic
```python
# src/infrastructure/web/routers/v2.py - WRONG
@router.post("/coins")
def create_coin(dto: CreateCoinDTO, db: Session = Depends(get_db)):
    # ❌ Business logic in router
    if dto.weight_g <= 0:
        raise ValueError("Invalid weight")

    # ❌ Direct ORM manipulation
    orm_coin = CoinModel(category=dto.category, ...)
    db.add(orm_coin)
    db.commit()

    return orm_coin
```

## Migration from V1 to V2

**V1 Architecture** (Legacy):
```
backend/app/
├── models/coin.py         # ORM models mixed with business logic
├── schemas/coin.py        # Pydantic schemas
├── routers/coins.py       # Business logic in routers
└── crud/coin.py           # CRUD operations
```

**V2 Architecture** (Current):
```
backend/src/
├── domain/
│   ├── coin.py            # Pure domain entity
│   └── repositories.py    # Repository interfaces (Protocols)
├── application/
│   └── commands/          # Use cases
│       └── create_coin.py
└── infrastructure/
    ├── persistence/
    │   ├── orm.py         # ORM models (separate from domain)
    │   └── repositories/
    │       └── coin_repository.py  # Concrete implementations
    └── web/
        ├── routers/v2.py  # Thin adapters
        └── dependencies.py # DI setup
```

**Key Differences**:
- V1: Business logic scattered in routers, crud, models
- V2: Business logic centralized in domain/ and application/
- V1: Direct ORM manipulation everywhere
- V2: Repository pattern with interfaces
- V1: Hard to test (coupled to database)
- V2: Easy to test (mock repositories)

---

**Next:** [03-BACKEND-MODULES.md](03-BACKEND-MODULES.md) - Detailed breakdown of backend modules
