# CoinStack AI Developer Guide

> A comprehensive reference for AI coding assistants working on the CoinStack V2 codebase (Clean Architecture).

## Quick Start - Essential Context

When starting a development session, load these files in order:

```
1. README.md (this file) - Navigation and overview
2. 01-OVERVIEW.md - Domain knowledge and tech stack
3. 02-CLEAN-ARCHITECTURE.md - V2 architecture principles
4. 08-CRITICAL-RULES.md - MANDATORY requirements
5. 06-FILE-LOCATIONS.md - Quick file reference
```

Then load the relevant guide based on your task:

| Task | Primary Guide | Supporting Guides |
|------|---------------|-------------------|
| **Backend work** | `03-BACKEND-MODULES.md` | `04-DOMAIN-ENTITIES.md`, `08-CODING-PATTERNS.md` |
| **Frontend work** | `04-FRONTEND-MODULES.md` | `11-FRONTEND-COMPONENTS.md`, `10-DESIGN-SYSTEM.md` |
| **UI/Design changes** | `10-DESIGN-SYSTEM.md` | `11-FRONTEND-COMPONENTS.md` |
| **UI/UX features** | `12-UI-UX-ROADMAP.md` | `11-FRONTEND-COMPONENTS.md` |
| **API integration** | `07-API-REFERENCE.md` | `06-DATA-FLOWS.md` |
| **Database schema** | `05-DATA-MODEL.md` | `09-TASK-RECIPES.md` |
| **Adding features** | `09-TASK-RECIPES.md` | Relevant module guide |

## Document Index

| File | Purpose | When to Use |
|------|---------|-------------|
| **Quick Reference** |
| [06-FILE-LOCATIONS.md](06-FILE-LOCATIONS.md) | Fast file/directory lookup | Finding any file |
| [08-CRITICAL-RULES.md](08-CRITICAL-RULES.md) | **Mandatory requirements** | Before any code change |
| **Architecture** |
| [01-OVERVIEW.md](01-OVERVIEW.md) | Project context, domain terms, tech stack | Starting any task |
| [02-CLEAN-ARCHITECTURE.md](02-CLEAN-ARCHITECTURE.md) | V2 Clean Architecture principles | Understanding structure |
| **Backend** |
| [03-BACKEND-MODULES.md](03-BACKEND-MODULES.md) | Domain/Application/Infrastructure layers | Backend development |
| [04-DOMAIN-ENTITIES.md](04-DOMAIN-ENTITIES.md) | Entities, value objects, domain services | Working with domain logic |
| **Frontend & Design** |
| [04-FRONTEND-MODULES.md](04-FRONTEND-MODULES.md) | React architecture, hooks, stores | Frontend architecture |
| [10-DESIGN-SYSTEM.md](10-DESIGN-SYSTEM.md) | **Design tokens, colors, typography** | UI styling, theming |
| [11-FRONTEND-COMPONENTS.md](11-FRONTEND-COMPONENTS.md) | Component specs, patterns, usage | Building UI components |
| **Data & API** |
| [05-DATA-MODEL.md](05-DATA-MODEL.md) | Database schema, ORM models | Data layer changes |
| [07-API-REFERENCE.md](07-API-REFERENCE.md) | API endpoints, request/response | API integration |
| **Workflows** |
| [06-DATA-FLOWS.md](06-DATA-FLOWS.md) | Request flows, state management | Understanding processes |
| [08-CODING-PATTERNS.md](08-CODING-PATTERNS.md) | Code conventions and patterns | Writing new code |
| [09-TASK-RECIPES.md](09-TASK-RECIPES.md) | Step-by-step guides | Implementing features |
| [12-UI-UX-ROADMAP.md](12-UI-UX-ROADMAP.md) | **Planned features, backlog** | UI/UX enhancements |
| **UX/QA** |
| [../UX-UI-EXPLORATION-REPORT.md](../UX-UI-EXPLORATION-REPORT.md) | UX/UI exploration & API/routing evaluation | Pre-release review, consistency fixes |
| [../BROWSER-UX-FINDINGS.md](../BROWSER-UX-FINDINGS.md) | Browser-based UX validation (typical + corner cases) | Live-session findings, improvement ideas |
| [../BROWSER-UX-RECOMMENDATIONS-PLAN.md](../BROWSER-UX-RECOMMENDATIONS-PLAN.md) | Plan for browser findings (header search, palette, empty states, Add, image a11y) | Phased implementation steps, files, acceptance criteria |
| [../ACCESSIBILITY-CHECKLIST.md](../ACCESSIBILITY-CHECKLIST.md) | a11y checklist (keyboard, screen reader, contrast) | Accessibility audits |
| [../NUMISMATIC-EDGE-CASE-TEST-PLAN.md](../NUMISMATIC-EDGE-CASE-TEST-PLAN.md) | Numismatic edge cases (BC/AD, refs, die study) | Domain-specific QA |

## Project at a Glance

**CoinStack V2** is a personal ancient coin collection management system for numismatists, built with Clean Architecture principles.

### Tech Stack

```
Backend:  Python 3.12+ / FastAPI / SQLAlchemy 2.0 / SQLite
Frontend: React 18 / TypeScript 5.x / Vite / TanStack Query v5 / Zustand 4.x
UI:       Tailwind CSS / shadcn/ui
Testing:  pytest (backend) / Vitest + MSW (frontend)
```

### Project Structure (V2 - Clean Architecture)

```
coinstack/
├── backend/
│   └── src/
│       ├── domain/              # Domain Layer (no dependencies)
│       │   ├── coin.py          # Coin entity + value objects
│       │   ├── auction.py       # AuctionLot entity
│       │   ├── series.py        # Series entity
│       │   ├── vocab.py         # VocabTerm entity
│       │   ├── repositories.py  # Repository interfaces (Protocols)
│       │   ├── services/        # Domain services
│       │   └── strategies/      # Audit strategies
│       │
│       ├── application/         # Application Layer (use cases)
│       │   └── commands/
│       │       ├── create_coin.py
│       │       ├── enrich_coin.py
│       │       └── import_collection.py
│       │
│       └── infrastructure/      # Infrastructure Layer (external concerns)
│           ├── persistence/     # Database & ORM
│           │   ├── database.py
│           │   ├── orm.py       # Core ORM models
│           │   ├── models_vocab.py
│           │   ├── models_series.py
│           │   └── repositories/  # Concrete implementations
│           │
│           ├── scrapers/        # Auction scrapers
│           ├── services/        # Infrastructure services
│           └── web/             # FastAPI routers
│               ├── main.py      # FastAPI app
│               ├── dependencies.py
│               └── routers/
│
├── frontend/
│   └── src/
│       ├── App.tsx              # React entry point
│       ├── pages/               # Route pages
│       ├── components/          # React components
│       │   ├── ui/              # shadcn/ui
│       │   ├── layout/          # AppShell, Header, Sidebar
│       │   ├── coins/           # Coin-specific components
│       │   └── design-system/   # Badges, indicators
│       ├── hooks/               # TanStack Query hooks
│       ├── stores/              # Zustand stores (uiStore, filterStore)
│       ├── api/                 # API client + hooks
│       └── domain/              # TypeScript types (mirrors backend)
│
└── docs/
    └── ai-guide/                # This documentation
```

## Key Domain Concepts

| Term | Definition |
|------|------------|
| **Coin** | Aggregate root - central domain entity |
| **AuctionLot** | Scraped auction data entity |
| **Series** | Collection grouping (e.g., "Augustus Denarii") |
| **VocabTerm** | Controlled vocabulary (issuers, mints) |
| **Obverse** | Front of coin (usually portrait) |
| **Reverse** | Back of coin (design/legend) |
| **Legend** | Text inscribed on coin edge |
| **Mint** | Location where coin was struck |
| **Reference** | Catalog citation (RIC, RPC, Crawford) |
| **Denomination** | Coin type (Denarius, Aureus, Antoninianus) |

## Critical Rules (MUST FOLLOW)

### Documentation Protocol (MANDATORY)
1. **BEFORE changes**: Consult relevant guides in `docs/ai-guide/`
2. **AFTER changes**: Update guides to reflect modifications
3. Documentation is the source of truth - keep it accurate

### Ports (MANDATORY)
- **Backend: Port 8000** (FastAPI)
- **Frontend: Port 3000** (Vite)
- **Never** increment ports if busy - kill the process

### Git Authorship (MANDATORY)
- **Author**: `isayev <olexandr@olexandrisayev.com>`
- **NO** Co-authored-by trailers
- **NO** AI assistance mentions

### Database Safety (MANDATORY)
- **REQUIRED**: Timestamped backup to `backend/backups/` BEFORE schema changes
- **Format**: `coinstack_YYYYMMDD_HHMMSS.db`

### Architecture Rules (MANDATORY)
- Domain layer has ZERO dependencies
- Use cases depend on repository **interfaces** (Protocols), not implementations
- Repositories use `flush()`, not `commit()`
- Always use `selectinload()` for relationships (prevent N+1)

See [08-CRITICAL-RULES.md](08-CRITICAL-RULES.md) for complete requirements.

## Common Tasks Quick Reference

| Task | Key Files (V2 Paths) |
|------|----------------------|
| Add field to Coin | `src/domain/coin.py` → `src/infrastructure/persistence/orm.py` → `src/infrastructure/repositories/coin_repository.py` |
| New API endpoint | `src/infrastructure/web/routers/v2.py` → `src/application/commands/` |
| New domain entity | `src/domain/[entity].py` → `src/domain/repositories.py` (interface) |
| New scraper | `src/infrastructure/scrapers/[source]/scraper.py` → inherit from `base_playwright.py` |
| New React page | `src/pages/[Page].tsx` → `src/App.tsx` (routes) → `src/api/` (hooks) |
| Modify filters | `src/stores/filterStore.ts` → `src/api/v2.ts` (client) |

## Development Commands

### Backend (V2, uses uv)

```bash
cd backend

# Sync env: uv sync --all-extras  (first time or after dep changes)
# Start server (V2)
uv run run_server.py

# Run tests
uv run pytest tests -p pytest_asyncio         # All tests
uv run pytest -m unit                         # Unit tests only
uv run pytest -m integration                  # Integration tests only

# Type checking
uv run mypy src/

# Linting
uv run ruff check src/
```

### Frontend

```bash
cd frontend

# Start dev server
npm run dev              # Port 3000

# Run tests
npm test                 # Watch mode (Vitest)
npm run test:run         # Run once
npm run test:coverage    # With coverage

# Build & validation
npm run build            # TypeScript + Vite build
npm run typecheck        # TypeScript only
npm run lint             # ESLint
```

### Full Stack

```powershell
# Restart both servers (kills ports, starts fresh)
.\restart.ps1
```

## API Access Points

- **Frontend Dev**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Swagger Docs**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Database**: `backend/coinstack_v2.db` (SQLite)

## External Resources

### Auction Sites (Scrapers)

| Site | URL | Scraper Location |
|------|-----|------------------|
| Heritage Auctions | https://coins.ha.com | `src/infrastructure/scrapers/heritage/` |
| CNG | https://cngcoins.com | `src/infrastructure/scrapers/cng/` |
| Biddr | https://biddr.com | `src/infrastructure/scrapers/biddr/` |
| eBay | https://www.ebay.com | `src/infrastructure/scrapers/ebay/` |
| Agora Auctions | https://agoraauctions.com | `src/infrastructure/scrapers/agora/` |

### Reference Catalogs

| Catalog | Coverage | URL |
|---------|----------|-----|
| OCRE | RIC (Imperial) | http://numismatics.org/ocre/ |
| CRRO | Crawford (Republican) | http://numismatics.org/crro/ |
| RPC Online | Provincial/Greek Imperial | https://rpc.ashmus.ox.ac.uk/ |

### Grading Services

| Service | URL |
|---------|-----|
| NGC | https://www.ngccoin.com |
| PCGS | https://www.pcgs.com |

## Architecture Highlights (V2)

### Clean Architecture Layers

```
Domain Layer (src/domain/)
    ↓ depends on
Application Layer (src/application/)
    ↓ depends on
Infrastructure Layer (src/infrastructure/)
```

**Dependency Rule**: Dependencies flow INWARD only. Domain has ZERO external dependencies.

### Key Patterns

- **Repository Pattern**: Interfaces (Protocols) in domain, implementations in infrastructure
- **Dependency Injection**: FastAPI `Depends()` provides concrete implementations
- **Use Cases**: Application layer orchestrates domain entities via repository interfaces
- **Value Objects**: Immutable objects (Dimensions, Attribution, GradingDetails)
- **Aggregate Root**: Coin entity manages consistency of related entities

### Transaction Management

- **Automatic**: Managed by `get_db()` dependency
- **Repositories**: Use `flush()` to get IDs, never `commit()`
- **Auto-commit**: On successful request completion
- **Auto-rollback**: On exception

### N+1 Prevention

Always use eager loading:
```python
from sqlalchemy.orm import selectinload

orm_coin = self.session.query(CoinModel).options(
    selectinload(CoinModel.images)  # Eager load
).filter(CoinModel.id == coin_id).first()
```

## V1 Archive Note

**V1 Architecture** (archived, DO NOT MODIFY):
- Location: `backend/v1_archive/`
- Entry point: `app.main:app`
- Database: `backend/coinstack.db`

**V2 Architecture** (current, use this):
- Location: `backend/src/`
- Entry point: `src.infrastructure.web.main:app`
- Database: `backend/coinstack_v2.db`

---

**Start Here**: Load [08-CRITICAL-RULES.md](08-CRITICAL-RULES.md) before writing any code.

*Navigate to specific guides using the Document Index above.*
