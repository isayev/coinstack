# File Locations Quick Reference

## Critical Files

### Entry Points
- **Backend**: `backend/src/infrastructure/web/main.py` (FastAPI app, V2)
- **Frontend**: `frontend/src/main.tsx` (React entry point)
- **V1 Archive**: `backend/v1_archive/app/main.py` (legacy, DO NOT MODIFY)

### Database
- **V2 Database**: `backend/coinstack_v2.db` (current, canonical)
- **V1 Database**: `backend/coinstack.db` (legacy, archived)
- **Backups**: `backend/backups/coinstack_YYYYMMDD_HHMMSS.db`

### Configuration
- **Backend Env**: `backend/.env` (API keys, DB path)
- **Backend Deps**: `backend/pyproject.toml` (Python dependencies)
- **Frontend Deps**: `frontend/package.json` (Node dependencies)
- **Vite Config**: `frontend/vite.config.ts` (dev server, proxy)
- **Tailwind**: `frontend/tailwind.config.js` (design tokens)

### Project Rules
- **Main Guide**: `CLAUDE.md` (critical rules for AI assistants)
- **Architecture**: `ARCHITECTURE.md` (system design)
- **Cursor Rules**: `.cursor/rules/*.mdc` (Cursor IDE constraints)

## Backend V2 Structure (`backend/src/`)

### Domain Layer (`src/domain/`)
```
domain/
├── coin.py                    # Coin entity, value objects, enums
├── auction.py                 # AuctionLot entity
├── series.py                  # Series entity
├── vocab.py                   # VocabTerm entity
├── repositories.py            # Repository interfaces (Protocols)
│
└── services/
    ├── audit_engine.py        # Audit system coordinator
    ├── search_service.py      # Full-text search
    └── scraper_orchestrator.py # Scraper coordinator

└── strategies/
    ├── attribution_strategy.py # Attribution audit checks
    ├── physics_strategy.py     # Physical measurement checks
    ├── date_strategy.py        # Date validation checks
    └── grade_strategy.py       # Grading assessment checks
```

### Application Layer (`src/application/`)
```
application/
└── commands/
    ├── create_coin.py         # CreateCoinUseCase
    ├── enrich_coin.py         # EnrichCoinUseCase
    ├── import_collection.py   # ImportCollectionUseCase
    └── scrape_auction_lot.py  # ScrapeAuctionLotUseCase
```

### Infrastructure Layer (`src/infrastructure/`)
```
infrastructure/
├── persistence/
│   ├── database.py            # SQLAlchemy engine, session setup
│   ├── orm.py                 # CoinModel, CoinImageModel, AuctionDataModel
│   ├── models_vocab.py        # IssuerModel, MintModel
│   ├── models_series.py       # SeriesModel
│   │
│   └── repositories/
│       ├── coin_repository.py      # SqlAlchemyCoinRepository
│       ├── auction_data_repository.py # SqlAlchemyAuctionDataRepository
│       ├── vocab_repository.py     # SqlAlchemyVocabRepository
│       └── series_repository.py    # SqlAlchemySeriesRepository
│
├── scrapers/
│   ├── base_playwright.py     # Base scraper with Playwright
│   ├── heritage/
│   │   ├── scraper.py         # HeritageScraper (rich)
│   │   └── parser.py          # Heritage-specific parsing
│   ├── cng/
│   │   └── scraper.py         # CNGScraper (rich)
│   ├── biddr/
│   │   └── scraper.py         # BiddrScraper (rich)
│   ├── ebay/
│   │   └── scraper.py         # EBayScraper (rich)
│   └── agora/
│       ├── scraper.py         # AgoraScraper (rich)
│       └── parser.py
│
├── services/
│   ├── vocab_sync.py          # VocabSyncService
│   ├── series_service.py      # SeriesService
│   └── llm_service.py         # LLMService (AI enrichment)
│
├── scripts/
│   ├── add_indexes.py         # Add database indexes
│   ├── migrate_v1_to_v2_data.py # Data migration
│   └── fix_category_mapping.py  # Data cleanup
│
└── web/
    ├── main.py                # FastAPI app
    ├── dependencies.py        # Dependency injection
    │
    └── routers/
        ├── v2.py              # /api/v2/coins CRUD
        ├── vocab.py           # /api/v2/vocab
        ├── series.py          # /api/v2/series
        ├── scrape_v2.py       # /api/v2/scrape
        ├── audit_v2.py        # /api/v2/audit (planned)
        ├── llm.py             # /api/v2/llm (AI enrichment)
        ├── provenance.py      # /api/v2/provenance (planned)
        └── die_study.py       # /api/v2/die-study (planned)
```

## Frontend Structure (`frontend/src/`)

### Pages (`src/pages/`)
```
pages/
├── CollectionPage.tsx         # Main collection grid/table
├── CoinDetailPage.tsx         # Individual coin view
├── AddCoinPage.tsx            # Create new coin
├── EditCoinPage.tsx           # Edit existing coin
├── SettingsPage.tsx           # App settings
├── StatsPageV3.tsx            # Statistics dashboard
├── SeriesDashboard.tsx        # Series management
├── SeriesDetailPage.tsx       # Single series view
├── CreateSeriesPage.tsx       # Create new series
└── ReviewQueuePage.tsx        # AI review queue (planned)
```

### Components (`src/components/`)
```
components/
├── ui/                        # shadcn/ui components
│   ├── button.tsx
│   ├── card.tsx
│   ├── input.tsx
│   ├── select.tsx
│   ├── dialog.tsx
│   └── ... (30+ components)
│
├── layout/
│   ├── AppShell.tsx           # Main layout wrapper
│   ├── Header.tsx             # Top navigation
│   └── Sidebar.tsx            # Left sidebar
│
├── coins/
│   ├── CoinCardV3.tsx         # Card view (grid mode)
│   ├── CoinTableRowV3.tsx     # Table row (table mode)
│   ├── CoinForm.tsx           # Create/edit form
│   ├── CoinFilters.tsx        # Filter controls
│   └── VocabAutocomplete.tsx  # Controlled vocabulary autocomplete
│
├── design-system/
│   ├── colors.ts              # Design tokens
│   ├── MetalBadge.tsx         # Metal display
│   ├── CategoryBadge.tsx      # Category display
│   └── GradeBadge.tsx         # Grade display
│
└── features/
    └── collection/
        ├── CoinListV3.tsx     # Collection list logic
        ├── CoinDetailV3.tsx   # Coin detail logic
        └── CoinFilters.tsx    # Filter logic
```

### State Management (`src/stores/`)
```
stores/
├── uiStore.ts                 # UI state (sidebar, view mode)
├── filterStore.ts             # Filter state (Zustand)
└── columnStore.ts             # Table column visibility (Zustand)
```

### API Layer (`src/api/`)
```
api/
├── client.ts                  # Axios instance
├── v2.ts                      # V2 API client functions
└── queryKeys.ts               # TanStack Query key factory
```

### Hooks (`src/hooks/`)
```
hooks/
├── useCoins.ts                # TanStack Query for coins
├── useVocab.ts                # Vocabulary hooks
└── useSeries.ts               # Series hooks
```

### Domain Types (`src/domain/`)
```
domain/
└── schemas.ts                 # TypeScript types mirroring backend
```

## Testing

### Backend Tests (`backend/tests/`)
```
tests/
├── unit/
│   ├── domain/
│   │   ├── test_coin_domain.py
│   │   ├── test_vocab.py
│   │   └── test_series.py
│   │
│   └── infrastructure/
│       └── web/routers/
│           ├── test_vocab_router.py
│           └── test_series_router.py
│
└── integration/
    └── persistence/
        ├── test_vocab_models.py
        └── test_series_models.py
```

### Frontend Tests (`frontend/src/`)
```
src/
├── components/
│   └── coins/
│       └── CoinCard.test.tsx  # Colocated with component
│
└── mocks/
    ├── handlers.ts            # MSW request handlers
    └── server.ts              # MSW server setup
```

## Important Paths by Task

### Adding a New Field to Coin
1. Domain entity: `backend/src/domain/coin.py`
2. ORM model: `backend/src/infrastructure/persistence/orm.py`
3. Repository: `backend/src/infrastructure/repositories/coin_repository.py`
4. Frontend type: `frontend/src/domain/schemas.ts`
5. Frontend form: `frontend/src/components/coins/CoinForm.tsx`

### Adding a New API Endpoint
1. Router: `backend/src/infrastructure/web/routers/v2.py`
2. Use case (if needed): `backend/src/application/commands/`
3. Frontend client: `frontend/src/api/v2.ts`
4. Frontend hook: `frontend/src/hooks/useCoins.ts`

### Adding a New Scraper
1. Scraper class: `backend/src/infrastructure/scrapers/[source]/scraper.py`
2. Inherit from: `backend/src/infrastructure/scrapers/base_playwright.py`
3. Parser (if complex): `backend/src/infrastructure/scrapers/[source]/parser.py`
4. Router: `backend/src/infrastructure/web/routers/scrape_v2.py`

### Database Schema Change
1. **BACKUP FIRST**: `backend/backups/coinstack_YYYYMMDD_HHMMSS.db`
2. ORM models: `backend/src/infrastructure/persistence/orm.py`
3. Add indexes: `backend/src/infrastructure/scripts/add_indexes.py`
4. Migration script (if complex): `backend/src/infrastructure/scripts/`

### Adding Controlled Vocabulary
1. Domain entity: `backend/src/domain/vocab.py`
2. ORM model: `backend/src/infrastructure/persistence/models_vocab.py`
3. Repository: `backend/src/infrastructure/repositories/vocab_repository.py`
4. Router: `backend/src/infrastructure/web/routers/vocab.py`
5. Frontend autocomplete: `frontend/src/components/coins/VocabAutocomplete.tsx`

## Quick Command Reference

### Backend (uv)
```bash
# Start server (V2)
cd backend
uv run run_server.py

# Run tests
uv run pytest tests -p pytest_asyncio
uv run pytest -m unit
uv run pytest -m integration

# Type checking
uv run mypy src/

# Linting
uv run ruff check src/
```

### Frontend
```bash
# Start dev server
cd frontend
npm run dev  # Port 3000

# Run tests
npm test

# Build
npm run build

# Type check
npm run typecheck
```

### Full Stack
```powershell
# Restart both servers (kills ports, starts fresh)
.\restart.ps1
```

### Database
```bash
# Add indexes
cd backend
uv run python -m src.infrastructure.scripts.add_indexes --verify

# Backup database
uv run python -m src.infrastructure.scripts.backup_database
```

## File Naming Conventions

### Backend
- **Modules**: `lowercase_with_underscores.py`
- **Classes**: `PascalCase` (e.g., `CoinRepository`, `AuditEngine`)
- **Functions**: `lowercase_with_underscores` (e.g., `get_by_id`, `create_coin`)
- **Test files**: `test_*.py` (e.g., `test_coin_domain.py`)

### Frontend
- **Components**: `PascalCase.tsx` (e.g., `CoinCard.tsx`, `CoinForm.tsx`)
- **Hooks**: `camelCase.ts` with `use` prefix (e.g., `useCoins.ts`, `useVocab.ts`)
- **Stores**: `camelCase.ts` with `Store` suffix (e.g., `uiStore.ts`, `filterStore.ts`)
- **Utils**: `camelCase.ts` (e.g., `formatDate.ts`, `validation.ts`)
- **Test files**: `*.test.tsx` (e.g., `CoinCard.test.tsx`)

---

**Next:** [07-API-REFERENCE.md](07-API-REFERENCE.md) - Complete API endpoint documentation
