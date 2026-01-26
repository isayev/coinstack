# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Identity

**CoinStack** is a personal ancient coin collection management system for cataloging Roman, Greek, and Byzantine coins. Single-user desktop/web application with catalog integration, auction data scraping, and collection analytics.

## Critical Rules (STRICT ENFORCEMENT)

### Documentation Sync (ZERO TOLERANCE)
**THE MOST IMPORTANT RULE - READ THIS FIRST:**
- **BEFORE any code change**: Consult `design/` specs (UI) and `docs/ai-guide/` documents
- **AFTER any code change**: Update `docs/ai-guide/` to reflect ALL changes
- **See**: [DOCUMENTATION_RULES.md](DOCUMENTATION_RULES.md) for complete protocol
- **Enforcement**: `.cursor/rules/developer-guide.mdc` (always applies)
- **Why**: Documentation is the authoritative source of truth. Stale docs → wrong assumptions → bugs → tech debt.

**If you change code without updating docs, you are breaking the codebase.**

### Ports (MANDATORY)
- **Backend: Port 8000** (FastAPI/Uvicorn)
- **Frontend: Port 3000** (Vite dev server)
- **NEVER** increment ports. If port is busy, kill the process using it.
- Frontend proxy at `/api` always points to `http://localhost:8000`

### Git Authorship (MANDATORY)
- **Author**: `isayev <olexandr@olexandrisayev.com>`
- **NO Co-authored-by trailers** - all commits authored solely by repository owner
- **NO mentions of AI assistance** in commits, PRs, or code comments

### Database Safety (MANDATORY)
- **Database**: `backend/coinstack_v2.db` (SQLite)
- **REQUIRED**: Timestamped backup to `backend/backups/` BEFORE any schema change/migration
- **Format**: `coinstack_YYYYMMDD_HHMMSS.db`
- **Retention**: Keep rolling 5 backups, delete oldest when creating new

### Scraper Usage
- **ALWAYS use rich scrapers**: `heritage`, `cng`, `biddr`, `ebay` (in `backend/src/infrastructure/scrapers/`)
- Rich scrapers are Playwright-based with structured data extraction
- Avoid simple/legacy scrapers if rich version exists

## Architecture Overview

### Clean Architecture (V2)
The codebase follows Clean Architecture with clear separation of concerns:

```
Domain Layer (src/domain/)
├── Entities: Coin (Aggregate Root), AuctionLot, Series, Vocab
├── Value Objects: Dimensions, Attribution, GradingDetails, AcquisitionDetails
├── Services: AuditEngine, ScraperOrchestrator
├── Strategies: AttributionStrategy, PhysicsStrategy, DateStrategy, GradeStrategy
└── Interfaces: IScraper, ICollectionImporter, repositories

Application Layer (src/application/commands/)
├── CreateCoinUseCase
├── ImportCollectionUseCase
├── EnrichCoinUseCase
└── ScrapeAuctionLotUseCase

Infrastructure Layer (src/infrastructure/)
├── Persistence: SqlAlchemyCoinRepository, CoinModel (SQLAlchemy)
├── Importers: ExcelImporter
├── Scrapers: HeritageScraper, CNGScraper, BiddrScraper, EBayScraper
└── Web: FastAPI routers (v2, audit_v2, scrape_v2, vocab, series)
```

**Dependency Rule**: Domain has NO dependencies. Application depends on Domain. Infrastructure depends on both.

### Frontend Architecture
```
React 18 + TypeScript + Vite
├── State: TanStack Query (server), Zustand (UI/filters)
├── UI: Tailwind CSS + shadcn/ui components
├── Routing: React Router v6
└── Testing: Vitest + React Testing Library + MSW
```

**Key Patterns**:
- Feature-based structure in `src/features/` (collection, audit, scraper)
- Domain types in `src/domain/` mirroring backend
- API client in `src/api/`
- Mock service workers in `src/mocks/` for testing

## Development Commands

### Backend (Python 3.12+)

```bash
# Install dependencies (uses uv)
cd backend
pip install uv
uv sync

# Run development server (V2 Clean Architecture)
python -m uvicorn src.infrastructure.web.main:app --host 127.0.0.1 --port 8000 --reload

# Run tests (pytest with markers)
python -m pytest tests -p pytest_asyncio         # All tests
python -m pytest -m unit                         # Unit tests only
python -m pytest -m integration                  # Integration tests only
python -m pytest tests/unit/domain/test_vocab.py # Single test file

# Type checking
mypy src/

# Linting
ruff check src/
```

### Frontend (Node.js 18+)

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev                # Starts on port 3000

# Testing
npm test                   # Watch mode (Vitest)
npm run test:run           # Run once
npm run test:coverage      # With coverage report

# Build & validation
npm run build              # TypeScript compile + Vite build
npm run typecheck          # TypeScript type checking only
npm run lint               # ESLint
npm run preview            # Preview production build
```

### Full Stack

```bash
# Local development (kills ports, starts both servers)
.\restart.ps1              # PowerShell script for Windows

# Docker deployment
docker-compose up --build -d
# Access: Frontend http://localhost:3000, Backend http://localhost:8000/docs
```

## Key Domain Concepts

### Numismatic Terms
- **Denomination**: Coin type (Denarius, Antoninianus, Solidus, Aureus, etc.)
- **Metal**: gold, silver, bronze, billon, electrum, orichalcum, potin, lead, ae
- **Category**: imperial, republic, provincial, byzantine, greek, celtic, judaean
- **Obverse/Reverse**: Front (portrait) / Back (design/legend) of coin
- **Legend**: Inscribed text on coin (often abbreviated Latin)
- **Exergue**: Area below main reverse design
- **Die Axis**: Orientation between obverse/reverse (0-12h clock positions)
- **RIC/RPC/Crawford/Sear**: Reference catalog systems

### Data Model (Domain Entities)

**Coin** (Aggregate Root):
- Classification: category, denomination, metal, series
- People: issuing_authority, portrait_subject, dynasty, status
- Chronology: reign dates, mint year (with BC/AD handling)
- Physical: weight, diameter, die_axis
- Design: obverse/reverse legend/description, exergue
- Grading: grade_service (NGC/PCGS/self), grade, certification_number
- Acquisition: date, price, source, url
- Research: rarity, historical_significance, personal_notes

**Value Objects** (immutable):
- `Dimensions(weight_g, diameter_mm, die_axis)`
- `Attribution(issuing_authority, portrait_subject, dynasty, status)`
- `GradingDetails(service, grade, cert_number)`
- `AcquisitionDetails(date, price, source, url)`

### Audit System
The `AuditEngine` compares coins against reference data using pluggable strategies:
- **AttributionStrategy**: Checks issuing authority, portrait subject
- **PhysicsStrategy**: Validates weight, diameter within tolerances
- **DateStrategy**: Verifies mint year against reign dates
- **GradeStrategy**: Reviews grade vs expected for reference type

Audit results are color-coded: `green` (pass), `yellow` (warning), `red` (fail).

### Scraper System
**ScraperOrchestrator** coordinates auction house scrapers:
- Each scraper implements `IScraper` interface
- Returns `AuctionLot` with structured data
- Playwright-based for JavaScript rendering
- Handles pagination, image downloads, provenance parsing

Supported auction houses: Heritage, CNG, Biddr (+ sub-houses), eBay, Agora.

## API Structure

### Backend Routes (FastAPI)
```
/api/v2/coins              # CRUD operations (GET, POST, PUT, DELETE)
/api/v2/coins/{id}/audit   # Run audit on coin
/api/v2/scrape             # Scrape auction lot URL
/api/v2/vocab              # Vocabulary management (issuing authorities, mints)
/api/v2/series             # Series management (ruler/type groupings)
```

**Key Endpoints**:
- `GET /api/v2/coins?skip=0&limit=50&category=imperial&metal=silver` - List with filters
- `POST /api/v2/coins` - Create coin (body: CoinCreate schema)
- `GET /api/v2/coins/{id}` - Get single coin
- `PUT /api/v2/coins/{id}` - Update coin
- `DELETE /api/v2/coins/{id}` - Delete coin
- `POST /api/v2/coins/{id}/audit` - Run audit checks
- `POST /api/v2/scrape?url=...` - Scrape auction lot

### Frontend API Client
Located in `frontend/src/api/client.ts`, uses Axios with:
- Base URL: `/api` (proxied to backend by Vite)
- TanStack Query hooks in `src/api/` for each resource
- Request/response transformers for date handling

## Testing Strategy

### Backend Tests
Located in `backend/tests/`:
- **Unit tests** (`tests/unit/`): Fast, no DB, no I/O (marked `@pytest.mark.unit`)
- **Integration tests** (`tests/integration/`): DB interactions, external APIs (marked `@pytest.mark.integration`)

Test structure mirrors `src/` with domain, application, infrastructure layers.

**Running specific test types**:
```bash
pytest -m unit              # Only unit tests (fast)
pytest -m integration       # Only integration tests (slower, need DB)
```

### Frontend Tests
Located in `frontend/src/`:
- Vitest for test runner (Jest-compatible API)
- React Testing Library for component tests
- MSW (Mock Service Worker) for API mocking in `src/mocks/handlers.ts`
- Tests colocated with components: `ComponentName.test.tsx`

**Test globals** configured in `vite.config.ts` (no imports needed for describe/it/expect).

## File Conventions

### Backend Python
- Models (ORM): `backend/src/infrastructure/persistence/models/`
- Domain entities: `backend/src/domain/*.py`
- Use cases: `backend/src/application/commands/*.py`
- Routers: `backend/src/infrastructure/web/routers/*.py`
- Services: `backend/src/domain/services/*.py` or `backend/src/infrastructure/services/`

### Frontend TypeScript
- Path alias: `@/` maps to `src/`
- Components: PascalCase filenames (e.g., `CoinCard.tsx`)
- Hooks: camelCase with `use` prefix (e.g., `useCoins.ts`)
- Types: `src/types/` for shared types, `src/domain/` for domain models
- Pages: `src/pages/` (route components)

## Migration Notes

**V1 Archive**: The original app structure is preserved in `backend/v1_archive/` and uses `app.main:app` entry point. Do NOT modify V1 code.

**V2 Entry Point**: Current application uses `src.infrastructure.web.main:app` (Clean Architecture).

**Database Migration**: Data was migrated from `coinstack.db` (V1) to `coinstack_v2.db` (V2). Both databases may exist; V2 is canonical.

## Important Patterns

### Backend Dependency Injection
FastAPI dependencies in `src/infrastructure/web/dependencies.py`:
- `get_db()` - SQLAlchemy session
- `get_coin_repository()` - Repository instance
- Injected via `Depends()` in router functions

### Frontend Data Fetching
All server state via TanStack Query:
```typescript
const { data, isLoading, error } = useCoins({ category: 'imperial' })
```
- Automatic caching, refetching, background updates
- Mutation hooks invalidate queries on success
- Query keys in `src/api/queryKeys.ts`

### Excel Import Format
Expected columns (flexible naming, case-insensitive matching):
- `Ruler Issuer`, `Coin type`, `Category`, `Composition`
- `Minted` (handles BC/AD, ranges like "96-95 BC")
- `Reference` (parses "RIC I 207; Crawford 335/1c")
- `Obverse`, `Reverse`, `Weight`, `Diameter`
- `Condition`, `NGC Grade`, `Mint`
- `Amount Paid`, `Source`, `Link`

Text normalization preserves Greek characters while cleaning spaces/dashes.

## Database Architecture (V2)

### Schema Initialization
Database tables are created automatically when importing from `database.py`:
```python
from src.infrastructure.persistence.database import init_db
init_db()  # Creates all tables defined in ORM models
```

**Important**: All ORM model files MUST be imported in `database.py` for tables to be created:
- `orm.py` - Core models (CoinModel, CoinImageModel, AuctionDataModel)
- `models_vocab.py` - Vocabulary (IssuerModel, MintModel)
- `models_series.py` - Series management

### ORM Model Syntax (SQLAlchemy 2.0)
**Rule**: Use modern `Mapped[T]` + `mapped_column()` syntax for all ORM models.

**Pattern**:
```python
from typing import Optional, List
from decimal import Decimal
from datetime import date
from sqlalchemy import Integer, String, Numeric, Date, Boolean, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column
from src.infrastructure.persistence.models import Base

class CoinModel(Base):
    __tablename__ = "coins_v2"

    # Required fields (non-nullable)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category: Mapped[str] = mapped_column(String)
    metal: Mapped[str] = mapped_column(String)
    weight_g: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    # Optional fields (nullable)
    issuer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("issuers.id"), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    acquisition_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Relationships
    images: Mapped[List["CoinImageModel"]] = relationship(back_populates="coin", cascade="all, delete-orphan")
    issuer_rel: Mapped[Optional["IssuerModel"]] = relationship("src.infrastructure.persistence.models_vocab.IssuerModel")
```

**Key Rules**:
- **Non-nullable**: `field: Mapped[type] = mapped_column(...)`
- **Nullable**: `field: Mapped[Optional[type]] = mapped_column(..., nullable=True)`
- **One-to-Many**: `field: Mapped[List["Model"]] = relationship(...)`
- **One-to-One/Many-to-One**: `field: Mapped[Optional["Model"]] = relationship(...)`
- Always use type hints (enables mypy type checking)
- Import types: `Decimal` from `decimal`, `date` from `datetime`

**Why this matters**:
- Better type safety and IDE autocomplete
- mypy compatibility for type checking
- Modern SQLAlchemy 2.0 best practices
- Consistency with newer models (models_vocab.py, models_series.py)

### Foreign Key Enforcement
Foreign keys are ENABLED via SQLAlchemy event listener in `database.py`:
```python
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
```
This ensures referential integrity for all connections made through SQLAlchemy.

### Database Indexes
Critical indexes for query performance:
- `coins_v2`: issuer, category, metal, year_start, acquisition_date, grading_state
- `issuers`: canonical_name
- `series`: slug (unique)
- `auction_data_v2`: url (unique), coin_id

Run `python -m src.infrastructure.scripts.add_indexes --verify` to create/verify indexes.

### Transaction Management
**Rule**: Transactions are managed automatically by the `get_db()` dependency. Repositories should NEVER call `commit()` or `rollback()`.

**How it works**:
```python
# dependencies.py (automatic transaction management):
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()  # Auto-commit on success
    except Exception:
        db.rollback()  # Auto-rollback on error
        raise
    finally:
        db.close()

# Repository (CORRECT - use flush() not commit()):
def save(self, coin: Coin) -> Coin:
    merged = self.session.merge(orm_coin)
    self.session.flush()  # Get ID, but don't commit
    return self._to_domain(merged)

# Repository (INCORRECT - don't do this):
def delete(self, coin_id: int):
    self.session.delete(orm_coin)
    self.session.commit()  # ❌ WRONG - breaks transaction boundaries

# Router (CORRECT - transaction is automatic):
@router.post("/coins")
def create_coin(..., repo: ICoinRepository = Depends(get_coin_repo)):
    coin = use_case.execute(dto)  # Changes are flushed
    return coin  # Auto-committed via get_db() dependency
```

**Why this matters**:
- Multiple repository calls in one request are part of the same transaction
- Exceptions automatically roll back ALL changes
- Clean separation: repositories handle data access, dependency handles transactions

### Query Optimization (N+1 Prevention)
**Rule**: Always use eager loading for relationships to prevent N+1 query problems.

**Pattern**:
```python
from sqlalchemy.orm import selectinload

# Repository method (CORRECT - eager load):
def get_by_id(self, coin_id: int) -> Optional[Coin]:
    orm_coin = self.session.query(CoinModel).options(
        selectinload(CoinModel.images)  # Eager load images
    ).filter(CoinModel.id == coin_id).first()
    return self._to_domain(orm_coin)

def get_all(self, skip: int = 0, limit: int = 100, ...) -> List[Coin]:
    query = self.session.query(CoinModel).options(
        selectinload(CoinModel.images)  # Eager load images
    )
    # ... sorting and filtering ...
    return [self._to_domain(c) for c in query.offset(skip).limit(limit).all()]
```

**Why this matters**:
- Without eager loading: 1 query for coins + N queries for images = O(n) queries
- With eager loading: 1 query for coins + 1 query for all images = O(1) queries
- Performance difference: 10-100x faster with large collections

### Repository Interfaces
**Rule**: Always depend on repository interfaces (Protocols), never on concrete implementations.

**Available Interfaces** (`src/domain/repositories.py`):
- `ICoinRepository` - Coin persistence
- `IAuctionDataRepository` - Auction lot persistence
- `ISeriesRepository` - Series/collection management
- `IVocabRepository` - Vocabulary (issuers, mints)

**Pattern**:
```python
# Use Case (CORRECT - depends on interface):
from src.domain.repositories import ICoinRepository

class CreateCoinUseCase:
    def __init__(self, repo: ICoinRepository):
        self.repo = repo

# Use Case (INCORRECT - depends on concrete class):
from src.infrastructure.repositories.coin_repository import SqlAlchemyCoinRepository

class CreateCoinUseCase:
    def __init__(self, repo: SqlAlchemyCoinRepository):  # ❌ WRONG
        self.repo = repo
```

**Why this matters**:
- Enables dependency injection and testing with mocks
- Loose coupling between layers (Clean Architecture)
- Can swap implementations without changing use cases

## Common Gotchas

1. **Port conflicts**: Always kill processes on 8000/3000 before restarting. Use `restart.ps1` to automate.
2. **Database backups**: Schema changes without backup violate critical rules. Always backup first to `backend/backups/`.
3. **Import paths**: Backend uses `src.` prefix (e.g., `from src.domain.coin import Coin`).
4. **Frontend proxy**: Vite dev server proxies `/api` to backend. In production, Nginx handles this.
5. **Test markers**: Backend tests MUST be marked `@pytest.mark.unit` or `@pytest.mark.integration`.
6. **BC/AD dates**: Years are stored as signed integers (negative for BC). Sort chronologically, not numerically.
7. **Git commits**: NO Co-authored-by trailers. Author must be `isayev <olexandr@olexandrisayev.com>`.
8. **Foreign Keys**: Always enabled for SQLAlchemy connections. Direct sqlite3 CLI shows disabled (different connection).
9. **Index Usage**: LIKE queries with leading wildcards (`%Augustus%`) cannot use indexes - this is expected SQLite behavior.

## Access Points

- **Frontend**: http://localhost:3000
- **Backend API Docs**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc (ReDoc)
- **Database**: `backend/coinstack_v2.db` (SQLite, can open with any SQLite viewer)

## Reference Documentation

### Quick References
- **API endpoints**: See Swagger UI at `/docs` when backend is running
- **Domain model**: `ARCHITECTURE.md` for entity relationships
- **README.md**: Feature list and tech stack overview
- **Cursor rules**: `.cursor/rules/*.mdc` for specific constraints (ports, git, database, scrapers)
- **GEMINI.md**: Condensed project context and rules summary

### Comprehensive AI Guide (`docs/ai-guide/`)

For detailed implementation guidance, see the comprehensive AI assistant documentation:

**Architecture & Design**:
- `02-architecture/clean-architecture.md` - V2 Clean Architecture layers in depth
- `02-architecture/domain-layer.md` - Domain entities, value objects, aggregates
- `02-architecture/application-layer.md` - Use cases and command handlers
- `02-architecture/infrastructure-layer.md` - Persistence, web, scrapers

**Development Guides**:
- `05-backend-modules/` - Domain entities, repositories, services, scrapers
- `06-frontend-modules/` - Components, state management, hooks, design system
- `07-coding-patterns/` - Backend and frontend conventions with examples

**API Reference**:
- `04-api/coins-api.md` - Coin CRUD operations
- `04-api/vocab-api.md` - Vocabulary management
- `04-api/series-api.md` - Series/collection endpoints
- `04-api/scraper-api.md` - Auction scraping operations

**Task Recipes** (Step-by-Step):
- `08-task-recipes/add-field.md` - Adding new coin fields
- `08-task-recipes/add-endpoint.md` - Creating API endpoints
- `08-task-recipes/add-scraper.md` - Adding new auction houses
- `08-task-recipes/database-migration.md` - Safe schema changes

**Systems Documentation**:
- `09-systems/scraper-system.md` - End-to-end scraping flow
- `09-systems/audit-system.md` - Audit engine and strategies
- `09-systems/vocab-system.md` - Controlled vocabulary and normalization

**Quick Lookups**:
- `10-reference/file-locations.md` - Complete file map
- `10-reference/enum-reference.md` - All enum values
- `10-reference/troubleshooting.md` - Common issues and solutions

**Note**: CLAUDE.md provides quick reference for immediate tasks. Consult `docs/ai-guide/` for comprehensive implementation details, patterns, and architectural context.
