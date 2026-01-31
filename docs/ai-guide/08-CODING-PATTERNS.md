# Coding Patterns and Conventions (V2 Clean Architecture)

## Architecture Principles

### Clean Architecture Layers

```
┌─────────────────────────────────────────┐
│  Infrastructure (Framework-specific)   │
│  - Web routers, ORM, scrapers          │
└───────────────┬─────────────────────────┘
                │ depends on
┌───────────────▼─────────────────────────┐
│  Application (Use cases)                │
│  - Business workflows                   │
└───────────────┬─────────────────────────┘
                │ depends on
┌───────────────▼─────────────────────────┐
│  Domain (Core business logic)           │
│  - Entities, value objects, services    │
│  - NO dependencies                      │
└─────────────────────────────────────────┘
```

**Dependency Rule**: Dependencies flow INWARD only. Domain has ZERO external dependencies.

---

## Python/Backend Conventions

### File Organization (V2)

```
src/
├── domain/                    # Pure business logic
│   ├── coin.py                # Entities + value objects + enums
│   ├── auction.py
│   ├── series.py
│   ├── vocab.py
│   ├── repositories.py        # Repository interfaces (Protocols)
│   ├── services/              # Domain services
│   │   ├── audit_engine.py
│   │   └── search_service.py
│   └── strategies/            # Strategy pattern
│       └── attribution_strategy.py
│
├── application/               # Use cases
│   └── commands/
│       ├── create_coin.py     # CreateCoinUseCase
│       └── enrich_coin.py     # EnrichCoinUseCase
│
└── infrastructure/            # External concerns
    ├── persistence/           # Database layer
    │   ├── database.py        # SQLAlchemy setup
    │   ├── orm.py             # ORM models
    │   ├── models_vocab.py
    │   └── repositories/      # Concrete implementations
    │       └── coin_repository.py
    │
    ├── scrapers/              # External integrations
    │   └── heritage/scraper.py
    │
    ├── services/              # Infrastructure services
    │   └── vocab_sync.py
    │
    └── web/                   # Web framework
        ├── main.py            # FastAPI app
        ├── dependencies.py    # DI setup
        └── routers/
            └── v2.py          # HTTP endpoints
```

### Naming Conventions

| Item | Convention | Example |
|------|------------|---------|
| Files | snake_case | `coin_repository.py` |
| Classes | PascalCase | `CoinRepository` |
| Functions | snake_case | `get_coin_by_id` |
| Variables | snake_case | `coin_list` |
| Constants | UPPER_SNAKE | `DEFAULT_PAGE_SIZE` |
| Enums | PascalCase class, lowercase values | `class Metal(str, Enum): gold = "gold"` |
| Protocols | I prefix (optional) | `ICoinRepository` or `CoinRepository` |

### Import Conventions (V2)

**ALWAYS use `src.` prefix for backend imports**:

```python
# ✅ CORRECT - V2 imports
from src.domain.coin import Coin
from src.domain.repositories import ICoinRepository
from src.infrastructure.persistence.orm import CoinModel
from src.application.commands.create_coin import CreateCoinUseCase

# ❌ WRONG - V1 imports
from app.models.coin import Coin
from app.crud.coin import get_coin
```

---

## Domain Layer Patterns

### Domain Entity Pattern

**Rules**:
- Pure Python dataclasses
- NO dependencies on SQLAlchemy, FastAPI, Pydantic
- Contains business logic and validation
- Aggregate roots manage consistency

```python
# src/domain/coin.py
from dataclasses import dataclass, field
from typing import Optional, List
from decimal import Decimal
from datetime import date
from enum import Enum

# Enums (domain vocabulary)
class Category(str, Enum):
    REPUBLIC = "republic"
    IMPERIAL = "imperial"
    PROVINCIAL = "provincial"
    BYZANTINE = "byzantine"

class Metal(str, Enum):
    GOLD = "gold"
    SILVER = "silver"
    BRONZE = "bronze"
    BILLON = "billon"

# Value Object (immutable)
@dataclass(frozen=True)
class Dimensions:
    """Value object for physical measurements."""
    weight_g: Optional[Decimal]
    diameter_mm: Optional[Decimal]
    die_axis: Optional[int]

    def __post_init__(self):
        """Validate on construction."""
        if self.weight_g and self.weight_g <= 0:
            raise ValueError("Weight must be positive")
        if self.diameter_mm and self.diameter_mm <= 0:
            raise ValueError("Diameter must be positive")

# Entity (mutable, has identity)
@dataclass
class Coin:
    """Coin aggregate root - central domain entity."""

    # Identity
    id: Optional[int]

    # Classification (required)
    category: str
    denomination: str
    metal: str

    # Attribution
    issuing_authority: Optional[str] = None
    portrait_subject: Optional[str] = None

    # Physical
    weight_g: Optional[Decimal] = None
    diameter_mm: Optional[Decimal] = None
    die_axis: Optional[int] = None

    # Collections
    images: List['CoinImage'] = field(default_factory=list)
    references: List['CoinReference'] = field(default_factory=list)

    # Value Objects
    dimensions: Optional[Dimensions] = None

    def validate(self) -> List[str]:
        """Domain validation logic."""
        errors = []

        if not self.category:
            errors.append("Category is required")

        if self.weight_g and self.weight_g <= 0:
            errors.append("Weight must be positive")

        if self.diameter_mm and self.diameter_mm <= 0:
            errors.append("Diameter must be positive")

        return errors

    def is_imperial(self) -> bool:
        """Business logic method."""
        return self.category == Category.IMPERIAL.value

    def is_professionally_graded(self) -> bool:
        """Check if coin has professional grading."""
        return hasattr(self, 'grade_service') and self.grade_service in ['ngc', 'pcgs']
```

### Repository Interface Pattern (Protocol)

**Rules**:
- Define in `src/domain/repositories.py`
- Use `typing.Protocol` for interface definition
- NO implementation details

```python
# src/domain/repositories.py
from typing import Protocol, Optional, List
from src.domain.coin import Coin

class ICoinRepository(Protocol):
    """Repository interface for coin persistence."""

    def get_by_id(self, coin_id: int) -> Optional[Coin]:
        """Get coin by ID."""
        ...

    def save(self, coin: Coin) -> Coin:
        """Save coin (create or update)."""
        ...

    def delete(self, coin_id: int) -> None:
        """Delete coin."""
        ...

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> List[Coin]:
        """Get filtered coins."""
        ...

    def count(self, **filters) -> int:
        """Count coins matching filters."""
        ...
```

### Domain Service Pattern

**Rules**:
- Contains business logic that doesn't fit a single entity
- NO dependencies on infrastructure
- Can use other domain services

```python
# src/domain/services/audit_engine.py
from typing import List
from src.domain.coin import Coin
from src.domain.auction import AuctionLot
from dataclasses import dataclass

@dataclass
class AuditResult:
    """Value object for audit result."""
    field: str
    status: str  # "green", "yellow", "red"
    message: Optional[str] = None

class AuditStrategy(Protocol):
    """Interface for audit strategies."""
    def check(self, coin: Coin, reference: AuctionLot) -> AuditResult:
        ...

class AuditEngine:
    """Domain service for auditing coins (no dependencies)."""

    def __init__(self, strategies: List[AuditStrategy]):
        self.strategies = strategies

    def audit_coin(self, coin: Coin, reference: AuctionLot) -> List[AuditResult]:
        """Run all audit strategies."""
        results = []
        for strategy in self.strategies:
            result = strategy.check(coin, reference)
            results.append(result)
        return results
```

---

## Application Layer Patterns

### Use Case Pattern

**Rules**:
- Orchestrates domain entities and services
- Depends on repository **interfaces** (Protocols), not implementations
- Contains application-specific business rules
- NO framework dependencies (FastAPI, SQLAlchemy)

```python
# src/application/commands/create_coin.py
from dataclasses import dataclass
from typing import Optional
from decimal import Decimal
from src.domain.coin import Coin
from src.domain.repositories import ICoinRepository

@dataclass
class CreateCoinDTO:
    """Input DTO for use case."""
    category: str
    denomination: str
    metal: str
    weight_g: Optional[float] = None
    diameter_mm: Optional[float] = None
    issuing_authority: Optional[str] = None

class CreateCoinUseCase:
    """Use case: Create new coin in collection."""

    def __init__(self, coin_repo: ICoinRepository):  # Interface, not implementation
        self.coin_repo = coin_repo

    def execute(self, dto: CreateCoinDTO) -> Coin:
        """Execute use case."""
        # Build domain entity
        coin = Coin(
            id=None,
            category=dto.category,
            denomination=dto.denomination,
            metal=dto.metal,
            weight_g=Decimal(str(dto.weight_g)) if dto.weight_g else None,
            diameter_mm=Decimal(str(dto.diameter_mm)) if dto.diameter_mm else None,
            issuing_authority=dto.issuing_authority
        )

        # Domain validation
        errors = coin.validate()
        if errors:
            raise ValueError(f"Validation errors: {', '.join(errors)}")

        # Save via repository interface
        return self.coin_repo.save(coin)
```

### Application Service Pattern

**Rules**:
- Orchestrates repository operations for complex workflows
- Depends on repository **interfaces** (Protocols), not implementations
- Returns explicit result objects (e.g., `ValuationResult`, `AlertCheckResult`)
- NO framework dependencies (FastAPI, SQLAlchemy)

```python
# src/application/services/valuation_service.py
from dataclasses import dataclass
from typing import Optional, List
from decimal import Decimal
from src.domain.coin import CoinValuation, MarketPrice
from src.domain.repositories import IMarketPriceRepository, ICoinValuationRepository

@dataclass(frozen=True, slots=True)
class ValuationResult:
    """Explicit result object for valuation operation."""
    success: bool
    valuation: Optional[CoinValuation] = None
    error: Optional[str] = None

class ValuationService:
    """Application service for coin valuation workflows."""

    def __init__(
        self,
        market_repo: IMarketPriceRepository,   # ✅ Protocol interface
        valuation_repo: ICoinValuationRepository,  # ✅ Protocol interface
    ):
        self._market_repo = market_repo
        self._valuation_repo = valuation_repo

    def calculate_valuation(
        self,
        coin_id: int,
        attribution_key: str,
        grade_numeric: Optional[int] = None,
    ) -> ValuationResult:
        """Calculate current market value based on comparable sales."""
        market_price = self._market_repo.get_by_attribution_key(attribution_key)

        if not market_price:
            return ValuationResult(
                success=False,
                error=f"No market data for: {attribution_key}",
            )

        # Business logic for valuation...
        valuation = CoinValuation(coin_id=coin_id, ...)
        saved = self._valuation_repo.create(coin_id, valuation)

        return ValuationResult(success=True, valuation=saved)
```

**Testing Use Cases** (with mock repositories):

```python
# tests/unit/application/test_create_coin.py
from unittest.mock import Mock
import pytest
from src.application.commands.create_coin import CreateCoinUseCase, CreateCoinDTO

@pytest.mark.unit
def test_create_coin_use_case():
    # Mock repository
    mock_repo = Mock()
    mock_repo.save.return_value = Mock(id=1, category="imperial")

    # Create use case with mocked dependency
    use_case = CreateCoinUseCase(mock_repo)

    # Execute
    dto = CreateCoinDTO(
        category="imperial",
        denomination="Denarius",
        metal="silver"
    )
    result = use_case.execute(dto)

    # Verify
    assert mock_repo.save.called
    assert result.id == 1
```

---

## Infrastructure Layer Patterns

### ORM Model Pattern (V2)

**Rules**:
- Use SQLAlchemy 2.0 `Mapped[T]` syntax (MANDATORY)
- Separate from domain entities
- Located in `src/infrastructure/persistence/`

```python
# src/infrastructure/persistence/orm.py
from sqlalchemy import Integer, String, Numeric, Date, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from typing import Optional, List
from decimal import Decimal
from datetime import date
from src.infrastructure.persistence.database import Base

class CoinModel(Base):
    """ORM model (infrastructure concern, separate from domain)."""
    __tablename__ = "coins_v2"

    # Use SQLAlchemy 2.0 Mapped[T] syntax
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Required fields (non-nullable)
    category: Mapped[str] = mapped_column(String, index=True)
    denomination: Mapped[str] = mapped_column(String)
    metal: Mapped[str] = mapped_column(String, index=True)

    # Optional fields (nullable=True)
    issuing_authority: Mapped[Optional[str]] = mapped_column(String, index=True, nullable=True)
    portrait_subject: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Numeric fields
    weight_g: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    diameter_mm: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    die_axis: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships with eager loading support
    images: Mapped[List["CoinImageModel"]] = relationship(
        back_populates="coin",
        cascade="all, delete-orphan"
    )

    references: Mapped[List["CoinReferenceModel"]] = relationship(
        back_populates="coin",
        cascade="all, delete-orphan"
    )

class CoinImageModel(Base):
    """ORM model for coin images."""
    __tablename__ = "coin_images_v2"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    coin_id: Mapped[int] = mapped_column(Integer, ForeignKey("coins_v2.id"))
    image_type: Mapped[str] = mapped_column(String)
    file_path: Mapped[str] = mapped_column(String)

    coin: Mapped["CoinModel"] = relationship(back_populates="images")
```

### Repository Implementation Pattern

**Rules**:
- Implement repository interface from domain
- Convert between ORM models and domain entities
- Use `flush()` NOT `commit()` (CRITICAL)
- Use `selectinload()` for relationships (prevent N+1)

```python
# src/infrastructure/repositories/coin_repository.py
from sqlalchemy.orm import Session, selectinload
from typing import Optional, List
from src.domain.coin import Coin
from src.domain.repositories import ICoinRepository
from src.infrastructure.persistence.orm import CoinModel

class SqlAlchemyCoinRepository:
    """Concrete implementation of ICoinRepository."""

    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, coin_id: int) -> Optional[Coin]:
        """Get coin by ID with eager loading."""
        # CRITICAL: Use selectinload() to prevent N+1 queries
        orm_coin = self.session.query(CoinModel).options(
            selectinload(CoinModel.images),
            selectinload(CoinModel.references)
        ).filter(CoinModel.id == coin_id).first()

        return self._to_domain(orm_coin) if orm_coin else None

    def save(self, coin: Coin) -> Coin:
        """Save coin (create or update)."""
        orm_coin = self._to_orm(coin)
        merged = self.session.merge(orm_coin)

        # CRITICAL: Use flush() NOT commit()
        # Transaction is managed by get_db() dependency
        self.session.flush()

        return self._to_domain(merged)

    def delete(self, coin_id: int) -> None:
        """Delete coin."""
        orm_coin = self.session.query(CoinModel).filter(
            CoinModel.id == coin_id
        ).first()

        if orm_coin:
            self.session.delete(orm_coin)
            self.session.flush()  # flush() not commit()

    def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        **filters
    ) -> List[Coin]:
        """Get filtered coins with eager loading."""
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
            diameter_mm=orm_coin.diameter_mm,
            die_axis=orm_coin.die_axis,
            issuing_authority=orm_coin.issuing_authority,
            portrait_subject=orm_coin.portrait_subject,
            # Map images, references, etc.
        )

    def _to_orm(self, coin: Coin) -> CoinModel:
        """Convert domain entity to ORM model."""
        return CoinModel(
            id=coin.id,
            category=coin.category,
            denomination=coin.denomination,
            metal=coin.metal,
            weight_g=coin.weight_g,
            diameter_mm=coin.diameter_mm,
            die_axis=coin.die_axis,
            issuing_authority=coin.issuing_authority,
            portrait_subject=coin.portrait_subject,
        )
```

### Dependency Injection Pattern

**Rules**:
- Define in `src/infrastructure/web/dependencies.py`
- `get_db()` manages transactions automatically
- Provide concrete implementations of interfaces
- **Return Protocol types, not concrete types** (CRITICAL for Clean Architecture)

```python
# src/infrastructure/web/dependencies.py
from sqlalchemy.orm import Session
from typing import Generator
from fastapi import Depends
from src.domain.repositories import (
    ICoinRepository, IMarketPriceRepository, ICoinValuationRepository,
    IPriceAlertRepository, IWishlistItemRepository, IWishlistMatchRepository,
    ILLMEnrichmentRepository, IPromptTemplateRepository, ILLMFeedbackRepository,
    ILLMUsageRepository, IMarketDataPointRepository, ICensusSnapshotRepository,
)
from src.infrastructure.persistence.database import SessionLocal
from src.infrastructure.repositories.coin_repository import SqlAlchemyCoinRepository
from src.infrastructure.repositories.market_price_repository import SqlAlchemyMarketPriceRepository
from src.application.services.valuation_service import ValuationService

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

# ✅ CORRECT - Return Protocol type, not concrete type
def get_coin_repository(db: Session = Depends(get_db)) -> ICoinRepository:
    """Provides concrete repository implementation."""
    return SqlAlchemyCoinRepository(db)

def get_market_price_repo(db: Session = Depends(get_db)) -> IMarketPriceRepository:
    return SqlAlchemyMarketPriceRepository(db)

# ✅ CORRECT - Service factory returns service type
def get_valuation_service(db: Session = Depends(get_db)) -> ValuationService:
    """Build ValuationService with repository dependencies."""
    return ValuationService(
        market_repo=SqlAlchemyMarketPriceRepository(db),
        valuation_repo=SqlAlchemyCoinValuationRepository(db),
    )

# ❌ WRONG - Don't return concrete repository types
def get_market_price_repo(db: Session = Depends(get_db)) -> SqlAlchemyMarketPriceRepository:  # ❌
    return SqlAlchemyMarketPriceRepository(db)
```

### Web Router Pattern (Thin Adapter)

**Rules**:
- Router is a THIN adapter to use cases
- NO business logic in routers
- Use FastAPI dependencies for injection
- Pydantic schemas for web layer only

```python
# src/infrastructure/web/routers/v2.py
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from src.application.commands.create_coin import CreateCoinUseCase, CreateCoinDTO
from src.domain.repositories import ICoinRepository
from src.infrastructure.web.dependencies import get_coin_repository

router = APIRouter(prefix="/api/v2", tags=["coins"])

# Pydantic schema for web layer (FastAPI needs this)
class CoinResponse(BaseModel):
    id: int
    category: str
    denomination: str
    metal: str

    class Config:
        from_attributes = True

@router.post("/coins", response_model=CoinResponse, status_code=201)
def create_coin(
    dto: CreateCoinDTO,  # Pydantic schema from use case
    coin_repo: ICoinRepository = Depends(get_coin_repository)  # Injected
):
    """Create new coin (thin adapter to use case)."""
    # Create use case with injected dependency
    use_case = CreateCoinUseCase(coin_repo)

    try:
        # Execute use case
        coin = use_case.execute(dto)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Return domain entity (FastAPI auto-converts with from_attributes)
    return coin

@router.get("/coins/{coin_id}", response_model=CoinResponse)
def get_coin(
    coin_id: int,
    coin_repo: ICoinRepository = Depends(get_coin_repository)
):
    """Get coin by ID (thin adapter)."""
    coin = coin_repo.get_by_id(coin_id)
    if not coin:
        raise HTTPException(status_code=404, detail="Coin not found")
    return coin
```

---

## Common Anti-Patterns to Avoid

### ❌ Domain Depending on Infrastructure

```python
# ❌ WRONG - Domain entity depending on SQLAlchemy
from sqlalchemy import Column, String
from sqlalchemy.orm import Mapped

class Coin(Base):  # ❌ Inheriting from ORM Base
    __tablename__ = "coins"
    id: Mapped[int] = mapped_column(primary_key=True)  # ❌ SQLAlchemy in domain
```

```python
# ✅ CORRECT - Pure domain entity
from dataclasses import dataclass

@dataclass
class Coin:  # ✅ No ORM dependencies
    id: Optional[int]
    category: str
```

### ❌ Use Case Depending on Concrete Repository

```python
# ❌ WRONG - Use case depending on concrete class
from src.infrastructure.repositories.coin_repository import SqlAlchemyCoinRepository

class CreateCoinUseCase:
    def __init__(self, repo: SqlAlchemyCoinRepository):  # ❌ Concrete class
        self.repo = repo
```

```python
# ✅ CORRECT - Use case depending on interface
from src.domain.repositories import ICoinRepository

class CreateCoinUseCase:
    def __init__(self, repo: ICoinRepository):  # ✅ Protocol interface
        self.repo = repo
```

### ❌ Repository Committing Transactions

```python
# ❌ WRONG - Repository committing
def save(self, coin: Coin) -> Coin:
    orm_coin = self._to_orm(coin)
    self.session.add(orm_coin)
    self.session.commit()  # ❌ Repository controls transaction
    return self._to_domain(orm_coin)
```

```python
# ✅ CORRECT - Repository uses flush()
def save(self, coin: Coin) -> Coin:
    orm_coin = self._to_orm(coin)
    merged = self.session.merge(orm_coin)
    self.session.flush()  # ✅ Get ID, transaction managed by get_db()
    return self._to_domain(merged)
```

### ❌ Business Logic in Router

```python
# ❌ WRONG - Business logic in router
@router.post("/coins")
def create_coin(dto: CoinCreate, db: Session = Depends(get_db)):
    # ❌ Validation in router
    if dto.weight_g <= 0:
        raise HTTPException(400, "Invalid weight")

    # ❌ Direct ORM manipulation
    orm_coin = CoinModel(category=dto.category, ...)
    db.add(orm_coin)
    db.commit()
    return orm_coin
```

```python
# ✅ CORRECT - Router delegates to use case
@router.post("/coins")
def create_coin(
    dto: CreateCoinDTO,
    coin_repo: ICoinRepository = Depends(get_coin_repository)
):
    use_case = CreateCoinUseCase(coin_repo)  # ✅ Use case has logic
    coin = use_case.execute(dto)  # ✅ Validation in domain/use case
    return coin
```

### ❌ Lazy Loading (N+1 Queries)

```python
# ❌ WRONG - Lazy loading causes N+1
def get_by_id(self, coin_id: int) -> Optional[Coin]:
    orm_coin = self.session.query(CoinModel).filter(
        CoinModel.id == coin_id
    ).first()  # ❌ No eager loading
    return self._to_domain(orm_coin)  # ❌ Will trigger N queries for images
```

```python
# ✅ CORRECT - Eager loading with selectinload()
from sqlalchemy.orm import selectinload

def get_by_id(self, coin_id: int) -> Optional[Coin]:
    orm_coin = self.session.query(CoinModel).options(
        selectinload(CoinModel.images),  # ✅ Eager load in 1 query
        selectinload(CoinModel.references)
    ).filter(CoinModel.id == coin_id).first()
    return self._to_domain(orm_coin)
```

---

## TypeScript/Frontend Conventions

> **Design System**: See [10-DESIGN-SYSTEM.md](10-DESIGN-SYSTEM.md) for colors, tokens, and component specs.
> **Components**: See [11-FRONTEND-COMPONENTS.md](11-FRONTEND-COMPONENTS.md) for detailed component reference.

### File Organization

```
src/
├── pages/                     # Route components
│   └── CollectionPage.tsx
├── components/
│   ├── ui/                    # shadcn/ui components
│   │   └── badges/            # MetalBadge, GradeBadge
│   ├── layout/                # AppShell, Header, Sidebar
│   ├── coins/                 # CoinCardV3, CoinForm
│   ├── dashboard/             # Dashboard widgets
│   └── design-system/         # Design primitives
├── features/
│   └── collection/            # Collection-specific components
│       ├── CoinListV3.tsx
│       ├── CollectionDashboard/
│       └── CollectionToolbar/
├── api/                       # API client + hooks
│   ├── client.ts              # Axios instance
│   └── v2.ts                  # TanStack Query hooks
├── stores/                    # Zustand stores
│   ├── uiStore.ts             # UI state
│   └── filterStore.ts         # Filters + pagination
├── domain/                    # TypeScript types (mirror backend)
│   └── schemas.ts             # Zod schemas
└── hooks/                     # Custom React hooks
    ├── useCoins.ts
    └── useSeries.ts
```

### Component Pattern

```typescript
// Import using @/ alias
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { MetalBadge } from '@/components/design-system/MetalBadge'
import { Coin } from '@/domain/schemas'

interface CoinCardProps {
  coin: Coin
  onClick?: () => void
  className?: string
}

export function CoinCard({ coin, onClick, className }: CoinCardProps) {
  return (
    <Card className={cn('cursor-pointer', className)} onClick={onClick}>
      <CardHeader>
        <img
          src={coin.image_url || '/placeholder.jpg'}
          alt={coin.denomination || 'Coin'}
          className="w-full h-40 object-cover rounded"
        />
      </CardHeader>
      <CardContent>
        <h3 className="font-medium">{coin.issuing_authority}</h3>
        <p className="text-sm text-muted-foreground">{coin.denomination}</p>
        {coin.metal && <MetalBadge metal={coin.metal} />}
      </CardContent>
    </Card>
  )
}
```

### TanStack Query Hook Pattern

```typescript
// src/api/v2.ts
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { apiClient } from './client'
import { Coin } from '@/domain/schemas'

export function useCoins(filters?: {
  category?: string
  metal?: string
}) {
  return useQuery({
    queryKey: ['coins', filters],
    queryFn: async () => {
      const { data } = await apiClient.get<Coin[]>('/api/v2/coins', {
        params: filters
      })
      return data
    },
    staleTime: 5 * 60 * 1000  // 5 minutes
  })
}

export function useCreateCoin() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (coin: Partial<Coin>) => {
      const { data } = await apiClient.post<Coin>('/api/v2/coins', coin)
      return data
    },
    onSuccess: () => {
      // Invalidate and refetch
      queryClient.invalidateQueries({ queryKey: ['coins'] })
    }
  })
}
```

### Zustand Store Pattern

```typescript
// src/stores/uiStore.ts
import { create } from 'zustand'
import { persist } from 'zustand/middleware'

interface UIState {
  sidebarOpen: boolean
  viewMode: 'grid' | 'table'
  setSidebarOpen: (open: boolean) => void
  setViewMode: (mode: 'grid' | 'table') => void
}

export const useUIStore = create<UIState>()(
  persist(
    (set) => ({
      sidebarOpen: true,
      viewMode: 'grid',
      setSidebarOpen: (open) => set({ sidebarOpen: open }),
      setViewMode: (mode) => set({ viewMode: mode })
    }),
    {
      name: 'ui-storage'  // localStorage key
    }
  )
)
```

---

## Testing Patterns

### Backend Unit Tests (Domain)

```python
# tests/unit/domain/test_coin_domain.py
import pytest
from decimal import Decimal
from src.domain.coin import Coin, Dimensions

@pytest.mark.unit
def test_coin_validation():
    coin = Coin(
        id=None,
        category="imperial",
        denomination="Denarius",
        metal="silver",
        weight_g=Decimal("-1")  # Invalid
    )

    errors = coin.validate()

    assert "Weight must be positive" in errors

@pytest.mark.unit
def test_dimensions_value_object():
    dims = Dimensions(
        weight_g=Decimal("3.45"),
        diameter_mm=Decimal("19.2"),
        die_axis=6
    )

    assert dims.weight_g == Decimal("3.45")

    # Value objects are immutable
    with pytest.raises(AttributeError):
        dims.weight_g = Decimal("4.0")
```

### Backend Unit Tests (Use Cases with Mocks)

```python
# tests/unit/application/test_create_coin.py
from unittest.mock import Mock
import pytest
from src.application.commands.create_coin import CreateCoinUseCase, CreateCoinDTO

@pytest.mark.unit
def test_create_coin_use_case_success():
    # Mock repository
    mock_repo = Mock()
    mock_repo.save.return_value = Mock(id=1, category="imperial")

    use_case = CreateCoinUseCase(mock_repo)

    dto = CreateCoinDTO(
        category="imperial",
        denomination="Denarius",
        metal="silver"
    )

    result = use_case.execute(dto)

    assert mock_repo.save.called
    assert result.id == 1
```

### Backend Integration Tests

```python
# tests/integration/repositories/test_coin_repository.py
import pytest
from src.domain.coin import Coin
from src.infrastructure.repositories.coin_repository import SqlAlchemyCoinRepository

@pytest.mark.integration
def test_coin_repository_save(db_session):
    repo = SqlAlchemyCoinRepository(db_session)

    coin = Coin(
        id=None,
        category="imperial",
        denomination="Denarius",
        metal="silver"
    )

    saved = repo.save(coin)

    assert saved.id is not None
    assert saved.category == "imperial"
```

### Frontend Component Tests

```typescript
// src/components/coins/CoinCard.test.tsx
import { render, screen } from '@testing-library/react'
import { CoinCard } from './CoinCard'

describe('CoinCard', () => {
  it('renders coin information', () => {
    const coin = {
      id: 1,
      category: 'imperial',
      denomination: 'Denarius',
      metal: 'silver',
      issuing_authority: 'Augustus'
    }

    render(<CoinCard coin={coin} />)

    expect(screen.getByText('Augustus')).toBeInTheDocument()
    expect(screen.getByText('Denarius')).toBeInTheDocument()
  })
})
```

---

## Summary: Key Rules to Follow

### Clean Architecture
1. **Domain has NO dependencies** - pure Python/TypeScript
2. **Use cases depend on interfaces** - Protocols, not concrete classes
3. **Routers are thin adapters** - delegate to use cases

### Database
4. **Repositories use `flush()` not `commit()`** - transactions managed by `get_db()`
5. **Always use `selectinload()`** - prevent N+1 queries
6. **Use SQLAlchemy 2.0 `Mapped[T]` syntax** - mandatory for new code

### Testing
7. **Mark backend tests** - `@pytest.mark.unit` or `@pytest.mark.integration`
8. **Mock repository interfaces** - test use cases in isolation

### Imports
9. **Backend uses `src.` prefix** - not `app.`
10. **Frontend uses `@/` alias** - configured in tsconfig.json

See [08-CRITICAL-RULES.md](08-CRITICAL-RULES.md) for complete mandatory requirements.

---

**Previous:** [07-API-REFERENCE.md](07-API-REFERENCE.md) - API documentation
**Next:** [09-TASK-RECIPES.md](09-TASK-RECIPES.md) - Step-by-step task guides
