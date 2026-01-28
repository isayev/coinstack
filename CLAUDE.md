# CoinStack - Claude Code Guide

> **For Claude Code AI Assistant** - Complete project reference and workflow guide

---

## 🚨 START HERE - Critical Workflow

### Before ANY Code Change

1. **📖 READ** relevant documentation:
   - UI changes? → `design/` specs + `docs/ai-guide/10-DESIGN-SYSTEM.md`
   - Backend? → `docs/ai-guide/03-BACKEND-MODULES.md` + `08-CODING-PATTERNS.md`
   - API? → `docs/ai-guide/07-API-REFERENCE.md`
   - Database? → `docs/ai-guide/05-DATA-MODEL.md`

2. **✅ STATE** what you consulted:
   ```
   📖 CONSULTED BEFORE:
   - design/[file] - [what I learned]
   - docs/ai-guide/[file] - [relevant patterns]
   ```

3. **🔨 IMPLEMENT** following documented patterns

4. **✏️ UPDATE** documentation after changes:
   ```
   ✏️ UPDATED AFTER:
   - docs/ai-guide/[file] - [what changed]
   - ✅ VERIFIED: Docs match implementation
   ```

**📚 Full Protocol**: [DOCUMENTATION_RULES.md](DOCUMENTATION_RULES.md)

---

## Quick Navigation

| Need | Go To |
|------|-------|
| **Quick start** | [Development Commands](#development-commands) |
| **Architecture** | [Clean Architecture V2](#clean-architecture-v2) |
| **Critical rules** | [Mandatory Rules](#mandatory-rules-zero-tolerance) |
| **Domain concepts** | [Numismatic Terms](#numismatic-terms) |
| **API reference** | [Backend Routes](#backend-routes-fastapi) |
| **Database** | [Database Architecture](#database-architecture-v2) |
| **Testing** | [Testing Strategy](#testing-strategy) |
| **Common issues** | [Common Gotchas](#common-gotchas) |
| **Full guides** | `docs/ai-guide/README.md` |

---

## Mandatory Rules (ZERO TOLERANCE)

### 1. Documentation Sync (THE MOST IMPORTANT)

**BEFORE any code change:**
- ✅ Consult `design/` specs (for UI work)
- ✅ Consult `docs/ai-guide/` documents
- ✅ Understand existing patterns

**AFTER any code change:**
- ✅ Update `docs/ai-guide/` to reflect ALL changes
- ✅ Verify documentation matches implementation

**Why**: Documentation is the authoritative source of truth. Stale docs → wrong assumptions → bugs → tech debt.

**If you change code without updating docs, you are breaking the codebase.**

See: [DOCUMENTATION_RULES.md](DOCUMENTATION_RULES.md) | `.cursor/rules/developer-guide.mdc`

### 2. Ports (MANDATORY)

- **Backend: Port 8000** (FastAPI)
- **Frontend: Port 3000** (Vite)
- **NEVER** increment ports - kill the process if busy
- Use `.\restart.ps1` to restart both servers

### 3. Git Authorship (MANDATORY)

- **Author**: `isayev <olexandr@olexandrisayev.com>`
- **NO** Co-authored-by trailers
- **NO** AI assistance mentions in commits/PRs/comments

### 4. Database Safety (MANDATORY)

- **Database**: `backend/coinstack_v2.db`
- **REQUIRED**: Timestamped backup to `backend/backups/` BEFORE schema changes
- **Format**: `coinstack_YYYYMMDD_HHMMSS.db`

### 5. Architecture (MANDATORY)

- Domain layer has ZERO dependencies
- Repositories use `flush()`, NEVER `commit()`
- Use `selectinload()` for relationships (prevent N+1)
- Use cases depend on interfaces (Protocols), not concrete classes
- ORM models use `Mapped[T]` + `mapped_column()` syntax

---

## Project Overview

**CoinStack** is a personal ancient coin collection management system for cataloging Roman, Greek, and Byzantine coins. Built with Clean Architecture (V2).

### Tech Stack

```
Backend:  Python 3.12+ / FastAPI / SQLAlchemy 2.0 / SQLite
Frontend: React 18 / TypeScript 5.x / Vite / TanStack Query v5 / Zustand
UI:       Tailwind CSS / shadcn/ui
Testing:  pytest (backend) / Vitest + MSW (frontend)
```

### Access Points

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Database**: `backend/coinstack_v2.db`

---

## Clean Architecture (V2)

### Layer Structure

```
Domain Layer (src/domain/)           ← NO dependencies
    ↓ depends on
Application Layer (src/application/) ← Depends on Domain interfaces
    ↓ depends on
Infrastructure Layer (src/infrastructure/)  ← Implements interfaces
```

**Dependency Rule**: Dependencies flow INWARD only.

### Key Components

**Domain Layer** (`src/domain/`):
- **Entities**: Coin (Aggregate Root), AuctionLot, Series, VocabTerm
- **Value Objects**: Dimensions, Attribution, GradingDetails, AcquisitionDetails
- **Services**: AuditEngine, SearchService
- **Strategies**: AttributionStrategy, PhysicsStrategy, DateStrategy
- **Interfaces** (Protocols): ICoinRepository, IVocabRepository, ISeriesRepository

**Application Layer** (`src/application/commands/`):
- CreateCoinUseCase, UpdateCoinUseCase
- ImportCollectionUseCase, EnrichCoinUseCase
- ScrapeAuctionLotUseCase

**Infrastructure Layer** (`src/infrastructure/`):
- **Persistence**: ORM models, concrete repositories
- **Web**: FastAPI routers (v2, vocab, series, scrape_v2)
- **Scrapers**: Heritage, CNG, Biddr, eBay, Agora
- **Services**: VocabSyncService, SeriesService

### Frontend Architecture

```
React 18 + TypeScript + Vite
├── State: TanStack Query v5 (server), Zustand 4.x (UI/filters)
├── UI: Tailwind CSS + shadcn/ui
├── Forms: React Hook Form + Zod schemas
└── Testing: Vitest + React Testing Library + MSW
```

**Key Patterns**:
- Feature-based structure: `src/features/collection/`
- Domain types mirror backend: `src/domain/schemas.ts`
- API client with Zod validation: `src/api/v2.ts`
- TanStack Query hooks: `src/hooks/useCoins.ts`

---

## Development Commands

### Backend (Python 3.12+, uv)

```bash
cd backend

# Sync env (first time or after dependency changes)
uv sync --all-extras
uv run playwright install chromium   # if scrapers needed

# Start server (V2, uses uv)
uv run run_server.py

# Tests
uv run pytest tests -p pytest_asyncio    # All tests
uv run pytest -m unit                    # Unit only (fast)
uv run pytest -m integration             # Integration only

# Type checking & linting
uv run mypy src/
uv run ruff check src/
```

### Frontend (Node.js 18+)

```bash
cd frontend

# Start server (port 3000)
npm run dev

# Tests
npm test                # Watch mode
npm run test:run        # Run once
npm run test:coverage   # With coverage

# Build & validation
npm run build           # TypeScript + Vite
npm run typecheck       # TypeScript only
npm run lint            # ESLint
```

### Full Stack

```bash
# Restart both servers (Windows)
.\restart.ps1

# Docker deployment
docker-compose up --build -d
```

---

## Numismatic Terms

Essential domain vocabulary:

| Term | Definition |
|------|------------|
| **Denomination** | Coin type (Denarius, Antoninianus, Aureus, Solidus) |
| **Metal** | AU (gold), AR (silver), AE (bronze), BI (billon), EL (electrum) |
| **Category** | imperial, republic, provincial, byzantine, greek, celtic, judaean |
| **Obverse** | Front of coin (usually portrait) |
| **Reverse** | Back of coin (design/legend) |
| **Legend** | Inscribed text (often abbreviated Latin) |
| **Exergue** | Area below main reverse design |
| **Die Axis** | Orientation between obverse/reverse (0-12h clock) |
| **Script** | Language/script on coin (Latin, Greek) |
| **Reign Dates** | Years ruler was in power (negative for BC) |
| **Officina** | Mint workshop identifier |
| **Provenance** | Ownership history (auction appearances, collections) |
| **RIC/RPC/Crawford** | Reference catalog systems |

---

## Backend Routes (FastAPI)

### Core Endpoints

```
GET    /api/v2/coins                    # List coins (paginated, filterable)
POST   /api/v2/coins                    # Create coin
GET    /api/v2/coins/{id}               # Get single coin
PUT    /api/v2/coins/{id}               # Update coin
DELETE /api/v2/coins/{id}               # Delete coin
POST   /api/v2/coins/{id}/audit         # Run audit checks

POST   /api/v2/scrape?url=...           # Scrape auction lot

GET    /api/v2/vocab/{type}             # List vocabulary (issuers, mints)
POST   /api/v2/vocab/{type}             # Create vocabulary term
GET    /api/v2/vocab/search/{type}?q=   # Search vocabulary

GET    /api/v2/series                   # List series
POST   /api/v2/series                   # Create series
GET    /api/v2/series/{id}              # Get series details
```

**Examples**:
```bash
# List imperial silver coins
GET /api/v2/coins?category=imperial&metal=silver&limit=50

# Scrape Heritage auction
POST /api/v2/scrape?url=https://coins.ha.com/...

# Search issuers
GET /api/v2/vocab/search/issuer?q=Augustus
```

**Full API Reference**: `docs/ai-guide/07-API-REFERENCE.md`

---

## Database Architecture (V2)

### Critical Patterns

**1. ORM Models** - Use SQLAlchemy 2.0 `Mapped[T]` syntax:

```python
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional

class CoinModel(Base):
    __tablename__ = "coins_v2"

    # Required fields
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String)

    # Optional fields
    issuer_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    images: Mapped[List["CoinImageModel"]] = relationship(...)
```

**2. Transaction Management** - Automatic via `get_db()`:

```python
# ✅ CORRECT - Repositories use flush()
def save(self, coin: Coin) -> Coin:
    self.session.merge(orm_coin)
    self.session.flush()  # Get ID, but don't commit
    return self._to_domain(coin)

# ❌ WRONG - Never call commit() in repositories
def save(self, coin: Coin):
    self.session.commit()  # Breaks transaction boundaries!
```

**3. N+1 Prevention** - Always use eager loading:

```python
from sqlalchemy.orm import selectinload

# ✅ CORRECT - Eager load relationships
def get_by_id(self, coin_id: int) -> Optional[Coin]:
    return self.session.query(CoinModel).options(
        selectinload(CoinModel.images)  # 1 extra query for all images
    ).filter(CoinModel.id == coin_id).first()

# ❌ WRONG - Lazy loading causes N+1
def get_by_id(self, coin_id: int):
    return self.session.query(CoinModel).get(coin_id)  # N queries!
```

**4. Repository Interfaces** - Depend on Protocols:

```python
# ✅ CORRECT - Use case depends on interface
from src.domain.repositories import ICoinRepository

class CreateCoinUseCase:
    def __init__(self, repo: ICoinRepository):
        self.repo = repo

# ❌ WRONG - Depends on concrete implementation
from src.infrastructure.repositories.coin_repository import SqlAlchemyCoinRepository

class CreateCoinUseCase:
    def __init__(self, repo: SqlAlchemyCoinRepository):  # Tight coupling!
        self.repo = repo
```

**Full Database Guide**: `docs/ai-guide/05-DATA-MODEL.md`

---

## Testing Strategy

### Backend Tests

```bash
# Fast unit tests (no DB, no I/O)
pytest -m unit

# Integration tests (DB, external APIs)
pytest -m integration

# All tests
pytest tests -p pytest_asyncio
```

**Structure**:
- `tests/unit/` - Domain, application, infrastructure units
- `tests/integration/` - Database, API integration
- Mark tests: `@pytest.mark.unit` or `@pytest.mark.integration`

### Frontend Tests

```bash
# Watch mode
npm test

# Run once
npm run test:run

# Coverage report
npm run test:coverage
```

**Tools**:
- Vitest (test runner)
- React Testing Library (component tests)
- MSW (API mocking in `src/mocks/handlers.ts`)

---

## Common Gotchas

1. **Port conflicts**: Use `.\restart.ps1` to kill and restart servers
2. **Database backups**: ALWAYS backup before schema changes
3. **Import paths**: Backend uses `from src.` prefix
4. **Frontend proxy**: Vite proxies `/api` to `http://localhost:8000`
5. **Test markers**: MUST mark tests `@pytest.mark.unit` or `@pytest.mark.integration`
6. **BC/AD dates**: Stored as signed integers (negative for BC)
7. **Git commits**: Author MUST be `isayev <olexandr@olexandrisayev.com>`
8. **Repositories**: Use `flush()` NOT `commit()`
9. **Relationships**: ALWAYS use `selectinload()` for eager loading
10. **Documentation**: Update `docs/ai-guide/` after EVERY change

---

## File Locations Quick Reference

### Backend

| Component | Path |
|-----------|------|
| Domain entities | `backend/src/domain/*.py` |
| Use cases | `backend/src/application/commands/*.py` |
| ORM models | `backend/src/infrastructure/persistence/orm.py` |
| Repositories | `backend/src/infrastructure/repositories/*.py` |
| API routers | `backend/src/infrastructure/web/routers/*.py` |
| Scrapers | `backend/src/infrastructure/scrapers/*/scraper.py` |
| Tests | `backend/tests/unit/` or `backend/tests/integration/` |

### Frontend

| Component | Path |
|-----------|------|
| Pages (routes) | `frontend/src/pages/*.tsx` |
| Features | `frontend/src/features/collection/*.tsx` |
| Components | `frontend/src/components/coins/*.tsx` |
| API client | `frontend/src/api/v2.ts` |
| Hooks | `frontend/src/hooks/useCoins.ts` |
| Stores | `frontend/src/stores/uiStore.ts` |
| Domain types | `frontend/src/domain/schemas.ts` |
| Design specs | `design/*.md` |

**Full File Map**: `docs/ai-guide/06-FILE-LOCATIONS.md`

---

## Documentation Resources

### Essential Guides (Start Here)

| Guide | Purpose |
|-------|---------|
| **[DOCUMENTATION_RULES.md](DOCUMENTATION_RULES.md)** | **MANDATORY workflow protocol** |
| **[docs/ai-guide/README.md](docs/ai-guide/README.md)** | **Complete guide index** |
| [docs/ai-guide/08-CRITICAL-RULES.md](docs/ai-guide/08-CRITICAL-RULES.md) | Validation checklist |
| [docs/ai-guide/01-OVERVIEW.md](docs/ai-guide/01-OVERVIEW.md) | Project context |

### Architecture & Patterns

- `02-CLEAN-ARCHITECTURE.md` - V2 architecture principles
- `03-BACKEND-MODULES.md` - Domain/Application/Infrastructure layers
- `04-FRONTEND-MODULES.md` - React architecture
- `08-CODING-PATTERNS.md` - Backend/frontend conventions

### Data & API

- `05-DATA-MODEL.md` - Database schema, ORM models
- `06-DATA-FLOWS.md` - Request flows, state management
- `07-API-REFERENCE.md` - Complete API endpoint reference

### Design & UI

- `10-DESIGN-SYSTEM.md` - Design tokens, colors, typography
- `11-FRONTEND-COMPONENTS.md` - Component specifications
- `design/CoinStack Design System v3.0.md` - Master design spec
- `design/CoinStack Frontpage + Grid Design.md` - Grid layout

### Implementation Recipes

- `09-TASK-RECIPES.md` - Step-by-step guides for common tasks
  - Adding fields, API endpoints, scrapers
  - Database migrations, new components

---

## Migration Notes

**V1 Archive** (DO NOT MODIFY):
- Location: `backend/v1_archive/`
- Entry point: `app.main:app`
- Database: `backend/coinstack.db`

**V2 Current** (USE THIS):
- Location: `backend/src/`
- Entry point: `src.infrastructure.web.main:app`
- Database: `backend/coinstack_v2.db`

---

## Scraper System

**Always use rich scrapers** (Playwright-based):
- Heritage: `backend/src/infrastructure/scrapers/heritage/scraper.py`
- CNG: `backend/src/infrastructure/scrapers/cng/scraper.py`
- Biddr: `backend/src/infrastructure/scrapers/biddr/scraper.py`
- eBay: `backend/src/infrastructure/scrapers/ebay/scraper.py`

**Pattern**:
- Implement `IScraper` interface
- Return `AuctionLot` entity
- Handle pagination, images, provenance

**Full Guide**: `docs/ai-guide/` (search for scraper documentation)

---

## Quick Start Checklist

Starting a new task? Follow this:

1. [ ] Read `DOCUMENTATION_RULES.md`
2. [ ] Consult relevant `design/` specs (UI work)
3. [ ] Consult relevant `docs/ai-guide/` documents
4. [ ] Note existing patterns and constraints
5. [ ] Implement following documented conventions
6. [ ] Update `docs/ai-guide/` to reflect changes
7. [ ] Verify documentation matches implementation
8. [ ] State what you consulted/updated in your response

**Remember**: Documentation is the source of truth. Keep it current.

---

**Last Updated**: January 25, 2026
**Version**: V2 Clean Architecture
**Enforcement**: Zero tolerance for outdated documentation
