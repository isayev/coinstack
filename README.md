# CoinStack

> Personal ancient coin collection management system built with Clean Architecture (V2)

Comprehensive catalog integration, intelligent data enrichment, auction scraping, and collection analytics for Roman, Greek, and Byzantine numismatics.

---

## 🚨 For Developers & AI Assistants

**MANDATORY - Read BEFORE making ANY code changes:**

1. **[DOCUMENTATION_RULES.md](DOCUMENTATION_RULES.md)** - Zero tolerance documentation sync protocol
2. **[CLAUDE.md](CLAUDE.md)** - Complete project reference for Claude Code
3. **[docs/ai-guide/README.md](docs/ai-guide/README.md)** - Comprehensive developer guide index

**Critical Rule**: All code changes require:
- **BEFORE**: Consult `design/` specs (UI) + `docs/ai-guide/` documents
- **AFTER**: Update `docs/ai-guide/` to reflect changes

**Documentation is the authoritative source of truth. Stale docs break the codebase.**

---

## Quick Start

### Prerequisites

- **Python 3.12+** (backend)
- **Node.js 18+** (frontend)
- **Windows** (PowerShell scripts for restart)

### Development Setup

```bash
# Backend (V2 Clean Architecture)
cd backend
python -m uvicorn src.infrastructure.web.main:app --host 127.0.0.1 --port 8000 --reload

# Frontend (new terminal)
cd frontend
npm install
npm run dev

# Or use PowerShell restart script
.\restart.ps1
```

### Access Points

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Database**: `backend/coinstack_v2.db` (SQLite)

---

## Features

### Collection Management
- **Full metadata cataloging** - Denomination, metal, ruler, dates (BC/AD), legends, physical attributes
- **Controlled vocabulary** - Unified vocab system for issuers, mints, denominations
- **Series management** - Organize coins by ruler/type with completion tracking
- **Reference tracking** - RIC, RPC, Crawford, Sear, BMC catalog integration
- **Image management** - Multi-image support with obverse/reverse

### Data Enrichment
- **Auction scraping** - Heritage, CNG, Biddr, eBay (Playwright-based)
- **Catalog integration** - OCRE (RIC), CRRO (Crawford), RPC lookups
- **Legend expansion** - Dictionary + LLM-powered abbreviation expansion
- **Audit system** - Validate attribution, physics, dates, grades

### Analytics & Views
- **Statistics dashboard** - Collection value, distribution charts, trends
- **Advanced filtering** - Category, metal, ruler, mint, date range, grade, rarity
- **Multiple views** - Grid (cards), table (sortable), detail pages
- **BC/AD handling** - Proper chronological sorting with negative years

### Import/Export
- **Excel/CSV import** - Intelligent parsing with text normalization
- **Database backups** - Timestamped backups before schema changes
- **CSV export** - Collection data export

---

## Tech Stack

### Backend (Clean Architecture V2)

```
Python 3.12+ / FastAPI / SQLAlchemy 2.0 / SQLite
├── Domain Layer       - Entities, value objects, services (no dependencies)
├── Application Layer  - Use cases (depends on domain interfaces)
└── Infrastructure     - Persistence, scrapers, API (implements interfaces)
```

**Key Technologies**:
- **FastAPI** - Modern async web framework
- **SQLAlchemy 2.0** - ORM with `Mapped[T]` syntax
- **Pydantic 2.x** - Data validation
- **Playwright** - Web scraping
- **pytest** - Testing framework

### Frontend

```
React 18 / TypeScript 5.x / Vite
├── TanStack Query v5  - Server state (object-based config)
├── Zustand 4.x        - UI state
├── Tailwind + shadcn  - Styling components
└── Zod                - Runtime validation
```

**Key Technologies**:
- **Vite** - Fast build tool
- **React Hook Form** - Form management
- **Recharts** - Analytics charts
- **Vitest + MSW** - Testing

---

## Architecture Overview (V2)

### Clean Architecture Layers

```
Domain Layer (src/domain/)
├── Entities: Coin, AuctionLot, Series, VocabTerm
├── Value Objects: Dimensions, Attribution, GradingDetails
├── Services: AuditEngine, SearchService
└── Interfaces (Protocols): ICoinRepository, IVocabRepository

Application Layer (src/application/commands/)
├── CreateCoinUseCase, UpdateCoinUseCase
├── ImportCollectionUseCase, EnrichCoinUseCase
└── ScrapeAuctionLotUseCase

Infrastructure Layer (src/infrastructure/)
├── Persistence: ORM models, repositories
├── Web: FastAPI routers (v2, vocab, series, scrape_v2)
├── Scrapers: Heritage, CNG, Biddr, eBay, Agora
└── Services: VocabSyncService, SeriesService
```

**Dependency Rule**: Dependencies flow INWARD only. Domain has NO external dependencies.

### Project Structure

```
coinstack/
├── backend/
│   └── src/
│       ├── domain/              # Domain layer (entities, value objects)
│       │   ├── coin.py          # Coin aggregate root
│       │   ├── auction.py       # AuctionLot entity
│       │   ├── series.py        # Series entity
│       │   ├── vocab.py         # VocabTerm entity
│       │   ├── repositories.py  # Repository interfaces (Protocols)
│       │   ├── services/        # Domain services
│       │   └── strategies/      # Audit strategies
│       │
│       ├── application/         # Application layer (use cases)
│       │   └── commands/
│       │       ├── create_coin.py
│       │       ├── enrich_coin.py
│       │       └── import_collection.py
│       │
│       └── infrastructure/      # Infrastructure layer
│           ├── persistence/     # Database & ORM
│           │   ├── database.py
│           │   ├── orm.py       # Core ORM models
│           │   ├── models_vocab.py
│           │   └── models_series.py
│           ├── repositories/    # Concrete repository implementations
│           ├── scrapers/        # Auction house scrapers
│           ├── services/        # Infrastructure services
│           └── web/             # FastAPI application
│               ├── main.py      # App entry point
│               └── routers/     # API endpoints
│
├── frontend/
│   └── src/
│       ├── pages/               # Route pages
│       ├── features/            # Feature modules (collection, etc.)
│       ├── components/          # React components
│       │   ├── ui/              # shadcn/ui base components
│       │   ├── coins/           # Coin-specific components
│       │   └── layout/          # AppShell, Header, Sidebar
│       ├── hooks/               # TanStack Query hooks
│       ├── stores/              # Zustand stores (UI, filters)
│       ├── api/                 # API client + hooks
│       └── domain/              # TypeScript schemas (mirrors backend)
│
├── docs/
│   └── ai-guide/                # Comprehensive developer documentation
│       ├── README.md            # Guide index
│       ├── 01-OVERVIEW.md       # Project overview
│       ├── 02-CLEAN-ARCHITECTURE.md
│       ├── 03-BACKEND-MODULES.md
│       ├── 04-FRONTEND-MODULES.md
│       ├── 05-DATA-MODEL.md
│       ├── 07-API-REFERENCE.md
│       ├── 08-CRITICAL-RULES.md # MANDATORY rules
│       └── ...
│
├── design/                      # UI/UX specifications
│   ├── CoinStack Design System v3.0.md
│   ├── CoinStack Frontpage + Grid Design.md
│   └── ...
│
├── DOCUMENTATION_RULES.md       # MANDATORY sync protocol
├── CLAUDE.md                    # Claude Code reference
└── README.md                    # This file
```

---

## API Reference (V2)

### Core Endpoints

```
# Coins
GET    /api/v2/coins                    # List coins (paginated, filterable)
POST   /api/v2/coins                    # Create coin
GET    /api/v2/coins/{id}               # Get coin detail
PUT    /api/v2/coins/{id}               # Update coin
DELETE /api/v2/coins/{id}               # Delete coin
POST   /api/v2/coins/{id}/audit         # Run audit checks

# Vocabulary (V3 unified system)
GET    /api/v2/vocab/{type}             # List vocabulary terms
POST   /api/v2/vocab/{type}             # Create term
GET    /api/v2/vocab/search/{type}?q=   # FTS5 search
POST   /api/v2/vocab/normalize          # Normalize raw text

# Series
GET    /api/v2/series                   # List series
POST   /api/v2/series                   # Create series
GET    /api/v2/series/{id}              # Get series details
PUT    /api/v2/series/{id}              # Update series

# Scraping
POST   /api/v2/scrape?url=...           # Scrape auction lot
```

**Full API Reference**: `docs/ai-guide/07-API-REFERENCE.md`

**Interactive Docs**: http://localhost:8000/docs (Swagger UI)

---

## Key Concepts

### Numismatic Terminology

| Term | Definition |
|------|------------|
| **Denomination** | Coin type (Denarius, Antoninianus, Aureus, Solidus) |
| **Metal** | AU (gold), AR (silver), AE (bronze), BI (billon) |
| **Category** | imperial, republic, provincial, byzantine, greek, celtic |
| **Obverse** | Front of coin (usually portrait) |
| **Reverse** | Back of coin (design/legend) |
| **Legend** | Inscribed text (often abbreviated Latin) |
| **Die Axis** | Orientation between obverse/reverse (0-12h) |
| **RIC/RPC/Crawford** | Standard reference catalog systems |

### Domain Entities

**Coin** (Aggregate Root):
- Classification: category, denomination, metal, series
- Attribution: issuing_authority, portrait_subject, dynasty
- Chronology: reign dates, mint year (BC/AD handling)
- Physical: weight, diameter, die_axis
- Design: obverse/reverse legends, descriptions
- Grading: grade_service (NGC/PCGS/self), grade, cert number
- Acquisition: date, price, source, provenance

**Value Objects** (immutable):
- `Dimensions` - weight_g, diameter_mm, die_axis
- `Attribution` - issuing_authority, portrait_subject, dynasty
- `GradingDetails` - service, grade, certification_number
- `AcquisitionDetails` - date, price, source, url

---

## Development Workflow

### Critical Rules

1. **Ports** (MANDATORY):
   - Backend: Port **8000**
   - Frontend: Port **3000**
   - Never increment - use `.\restart.ps1`

2. **Git Authorship** (MANDATORY):
   - Author: `isayev <olexandr@olexandrisayev.com>`
   - NO Co-authored-by trailers
   - NO AI mentions

3. **Database Safety** (MANDATORY):
   - Backup to `backend/backups/` BEFORE schema changes
   - Format: `coinstack_YYYYMMDD_HHMMSS.db`

4. **Architecture** (MANDATORY):
   - Domain layer has ZERO dependencies
   - Repositories use `flush()`, NEVER `commit()`
   - Always use `selectinload()` for eager loading
   - ORM models use `Mapped[T]` syntax

### Testing

```bash
# Backend
cd backend
pytest -m unit              # Fast unit tests
pytest -m integration       # Integration tests
pytest tests                # All tests

# Frontend
cd frontend
npm test                    # Watch mode
npm run test:run            # Run once
npm run test:coverage       # With coverage
```

### Common Commands

```bash
# Restart both servers (Windows)
.\restart.ps1

# Backend type checking
cd backend
mypy src/

# Frontend type checking
cd frontend
npm run typecheck

# Database backups
python -m src.infrastructure.scripts.backup_db

# Verify indexes
python -m src.infrastructure.scripts.add_indexes --verify
```

---

## Documentation

### For AI Assistants

Start here in order:
1. **[DOCUMENTATION_RULES.md](DOCUMENTATION_RULES.md)** - Workflow protocol
2. **[CLAUDE.md](CLAUDE.md)** - Complete reference
3. **[docs/ai-guide/README.md](docs/ai-guide/README.md)** - Guide index
4. **[docs/ai-guide/08-CRITICAL-RULES.md](docs/ai-guide/08-CRITICAL-RULES.md)** - Validation checklist

### For Human Developers

**Architecture & Design**:
- `docs/ai-guide/02-CLEAN-ARCHITECTURE.md` - V2 architecture
- `docs/ai-guide/03-BACKEND-MODULES.md` - Backend layers
- `docs/ai-guide/04-FRONTEND-MODULES.md` - Frontend architecture
- `design/CoinStack Design System v3.0.md` - UI specifications

**Implementation**:
- `docs/ai-guide/08-CODING-PATTERNS.md` - Code conventions
- `docs/ai-guide/09-TASK-RECIPES.md` - Step-by-step guides
- `docs/ai-guide/05-DATA-MODEL.md` - Database schema
- `docs/ai-guide/07-API-REFERENCE.md` - Complete API docs

---

## Migration Notes

**V1 Archive** (deprecated - DO NOT MODIFY):
- Location: `backend/v1_archive/`
- Database: `backend/coinstack.db`

**V2 Current** (use this):
- Location: `backend/src/`
- Database: `backend/coinstack_v2.db`
- Entry point: `src.infrastructure.web.main:app`

---

## Changelog

### v2.0.0 (Current - Clean Architecture)
- ✅ **Clean Architecture V2** - Domain/Application/Infrastructure layers
- ✅ **Vocabulary V3** - Unified vocab system with FTS5 search
- ✅ **Series Management** - Collection groupings with completion tracking
- ✅ **Audit System** - Pluggable strategy-based validation
- ✅ **Rich Scrapers** - Playwright-based for Heritage, CNG, Biddr, eBay
- ✅ **TanStack Query v5** - Object-based configuration
- ✅ **Design System V3** - Complete token system with badges
- ✅ **Comprehensive Docs** - 288KB ai-guide documentation

### v0.2.0 (Legacy V1)
- Type-centric reference system
- Catalog integration (OCRE, CRRO, RPC)
- Legend expansion with LLM
- Bulk enrichment
- Advanced filtering

### v0.1.0 (Initial)
- Core CRUD operations
- Grid/table views
- Excel import
- Statistics dashboard

---

## License

Private project - All rights reserved.

## Author

**isayev** (olexandr@olexandrisayev.com)

---

**Last Updated**: January 25, 2026
**Version**: V2.0.0 (Clean Architecture)
**Documentation**: Zero tolerance enforcement - always keep docs synchronized with code
