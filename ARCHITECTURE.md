# CoinStack Architecture

## System Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│    Backend      │────▶│    Database     │
│  React + Vite   │     │    FastAPI      │     │     SQLite      │
│  localhost:3000 │     │  localhost:8000 │     │ coinstack_v2.db │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Clean Architecture (V2)

The codebase follows Clean Architecture with strict layer separation and dependency inversion.

```
┌─────────────────────────────────────────────────────────────────┐
│                    Infrastructure Layer                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Web API   │  │  Scrapers   │  │      Persistence        │  │
│  │  (FastAPI)  │  │ (Playwright)│  │ (SQLAlchemy + SQLite)   │  │
│  └──────┬──────┘  └──────┬──────┘  └───────────┬─────────────┘  │
└─────────┼────────────────┼─────────────────────┼────────────────┘
          │                │                     │
          ▼                ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Application Layer                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                     Use Cases                            │   │
│  │  CreateCoin │ ImportCollection │ EnrichCoin │ ScrapeLot  │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Domain Layer                               │
│  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌─────────────┐  │
│  │   Coin    │  │ AuctionLot│  │   Series  │  │    Vocab    │  │
│  │(Aggregate)│  │  (Entity) │  │  (Entity) │  │  (Entity)   │  │
│  └───────────┘  └───────────┘  └───────────┘  └─────────────┘  │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Value Objects: Dimensions, Attribution, Grading, Acquis  │ │
│  └───────────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Domain Services: AuditEngine, ScraperOrchestrator        │ │
│  └───────────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────────┐ │
│  │  Repository Interfaces (Protocols): ICoinRepository, etc  │ │
│  └───────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

**Dependency Rule**: Dependencies only point inward. Domain has NO external dependencies.

## Data Model

### Core Entities

```
Coin (Aggregate Root)
├── id, created_at, updated_at
├── Classification: category, denomination, metal, series
├── Attribution: issuing_authority, portrait_subject, dynasty, status
├── Chronology: reign_start/end, mint_year_start/end (BC as negative)
├── Physical: weight_g, diameter_mm, die_axis
├── Design: obverse/reverse legend, description, exergue
├── Grading: grade_service (NGC/PCGS/self), grade, certification_number
├── Acquisition: date, price, source, url
├── Storage: holder_type, storage_location
└── Research: rarity, historical_significance, personal_notes

Relationships:
├── CoinImage (1:N) - Obverse/reverse photos
├── CoinReference (1:N) - Catalog references (RIC, RPC, RSC)
├── AuctionData (1:1) - Scraped auction lot data
├── Series (N:1) - Collection grouping
└── Issuer (N:1) - Vocabulary reference

AuctionLot (Entity)
├── url, auction_house, lot_number
├── title, description
├── hammer_price, estimate_low/high
├── sale_date
└── images, provenance

Series (Entity)
├── name, slug, description
├── ruler, metal, mint
├── Coins (1:N)
└── cover_image_id

Vocab (Entity)
├── IssuerModel - Canonical issuing authorities
├── MintModel - Mint locations
└── Aliases and normalization
```

### Value Objects (Immutable)

```python
Dimensions(weight_g: Decimal, diameter_mm: Decimal, die_axis: int)
Attribution(issuing_authority: str, portrait_subject: str, dynasty: str, status: str)
GradingDetails(service: str, grade: str, cert_number: str)
AcquisitionDetails(date: date, price: Decimal, source: str, url: str)
```

### Enums

- **Category**: republic, imperial, provincial, byzantine, greek, celtic, judaean
- **Metal**: gold, silver, bronze, billon, electrum, orichalcum, potin, lead, ae
- **GradeService**: ngc, pcgs, self, dealer
- **Rarity**: common, scarce, rare, very_rare, extremely_rare, unique

## API Architecture

### Router Structure (V2)

```
/api/v2
├── /coins              # CRUD operations (GET, POST, PUT, DELETE)
├── /coins/{id}/audit   # Run audit checks
├── /scrape             # Scrape auction lot URL
├── /vocab              # Vocabulary management (issuers, mints)
└── /series             # Series management (groupings)
```

### Request Flow

```
HTTP Request
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                    FastAPI Router                           │
│         (v2.py, audit_v2.py, scrape_v2.py, etc.)           │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Dependencies                              │
│         (get_db, get_coin_repository, etc.)                 │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                     Use Case                                 │
│         (CreateCoinUseCase, EnrichCoinUseCase)              │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    Repository                                │
│         (SqlAlchemyCoinRepository)                          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    ORM Models                                │
│         (CoinModel, CoinImageModel, etc.)                   │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
                       SQLite DB
```

## Frontend Architecture

### Component Hierarchy

```
App
├── ThemeProvider
├── QueryClientProvider (TanStack Query)
└── BrowserRouter
    └── AppShell
        ├── Header (search, add button, theme toggle)
        ├── Sidebar (navigation)
        ├── CommandPalette (Cmd+K)
        └── Routes
            ├── CollectionPage (grid/table views)
            ├── CoinDetailPage
            ├── AddCoinPage / EditCoinPage
            ├── AuditPage
            ├── AuctionsPage
            ├── StatsPage
            ├── ImportPage
            ├── SeriesDashboard / SeriesDetailPage
            └── SettingsPage
```

### State Management

- **Server State**: TanStack Query (coins, stats, vocab, series)
- **UI State**: Zustand (sidebar, view mode, command palette)
- **Filter State**: Zustand with persistence (category, metal, etc.)
- **Column Config**: Zustand (table column visibility/order)

### Data Flow

```
Component
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│              Custom Hook (useCoins, useSeries)              │
│                    ↓                                        │
│              TanStack Query (useQuery, useMutation)         │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    API Client (v2.ts)                       │
│                    Axios → /api/v2/*                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
                    Vite Proxy → Backend
```

## File Structure

```
backend/
├── src/
│   ├── domain/                    # Domain Layer (NO dependencies)
│   │   ├── coin.py               # Coin aggregate root
│   │   ├── auction.py            # AuctionLot entity
│   │   ├── series.py             # Series entity
│   │   ├── vocab.py              # Vocabulary entities
│   │   ├── repositories.py       # Repository interfaces (Protocols)
│   │   ├── importer.py           # Importer interface
│   │   ├── audit.py              # AuditEngine
│   │   ├── services/             # Domain services
│   │   │   ├── scraper_orchestrator.py
│   │   │   ├── scraper_service.py
│   │   │   ├── search_service.py
│   │   │   └── legend_service.py
│   │   └── strategies/           # Audit strategies
│   │       ├── attribution_strategy.py
│   │       ├── physics_strategy.py
│   │       ├── date_strategy.py
│   │       └── grade_strategy.py
│   │
│   ├── application/               # Application Layer
│   │   └── commands/             # Use cases
│   │       ├── create_coin.py
│   │       ├── import_collection.py
│   │       ├── enrich_coin.py
│   │       └── scrape_lot.py
│   │
│   └── infrastructure/            # Infrastructure Layer
│       ├── config.py             # Environment settings
│       ├── persistence/          # Database
│       │   ├── database.py       # Engine, session, init
│       │   ├── orm.py            # CoinModel, CoinImageModel
│       │   ├── models_vocab.py   # IssuerModel, MintModel
│       │   └── models_series.py  # SeriesModel
│       ├── repositories/         # Repository implementations
│       │   ├── coin_repository.py
│       │   └── auction_data_repository.py
│       ├── importers/
│       │   └── excel_importer.py
│       ├── scrapers/             # Auction house scrapers
│       │   ├── base_playwright.py
│       │   ├── heritage/
│       │   ├── cng/
│       │   ├── biddr/
│       │   ├── ebay/
│       │   └── agora/
│       ├── services/             # Infrastructure services
│       │   ├── series_service.py
│       │   ├── vocab_sync.py
│       │   └── vocab_normalizer.py
│       ├── scripts/              # Migration/maintenance scripts
│       │   ├── migrate_v1_v2.py
│       │   ├── add_indexes.py
│       │   └── add_description_column.py
│       └── web/                  # FastAPI application
│           ├── main.py           # App entry point
│           ├── dependencies.py   # DI (get_db, get_repo)
│           └── routers/
│               ├── v2.py         # Coin CRUD
│               ├── audit_v2.py   # Audit endpoints
│               ├── scrape_v2.py  # Scraper endpoints
│               ├── vocab.py      # Vocabulary
│               └── series.py     # Series management
│
└── tests/
    ├── unit/                     # Fast, no I/O
    │   ├── domain/
    │   ├── application/
    │   └── infrastructure/
    └── integration/              # Database tests
        └── persistence/

frontend/
└── src/
    ├── main.tsx                  # Entry point
    ├── App.tsx                   # Root component, routing
    ├── domain/                   # Domain types (mirrors backend)
    │   └── schemas.ts
    ├── api/                      # API client
    │   ├── api.ts               # Axios config
    │   └── v2.ts                # V2 endpoints
    ├── hooks/                    # React Query hooks
    │   ├── useCoins.ts
    │   ├── useSeries.ts
    │   ├── useAuctions.ts
    │   ├── useAudit.ts
    │   └── ...
    ├── stores/                   # Zustand stores
    │   ├── filterStore.ts
    │   ├── uiStore.ts
    │   └── columnStore.ts
    ├── pages/                    # Route components
    │   ├── CollectionPage.tsx
    │   ├── CoinDetailPage.tsx
    │   ├── AuditPage.tsx
    │   ├── SeriesDashboard.tsx
    │   └── ...
    ├── features/                 # Feature modules
    │   ├── collection/
    │   ├── audit/
    │   └── scraper/
    ├── components/
    │   ├── ui/                  # shadcn/ui components
    │   ├── layout/              # App shell
    │   ├── coins/               # Coin-specific
    │   ├── audit/               # Audit UI
    │   ├── auctions/            # Auction UI
    │   ├── import/              # Import UI
    │   └── design-system/       # Custom design tokens
    ├── lib/                      # Utilities
    │   ├── utils.ts
    │   └── formatters.ts
    ├── mocks/                    # MSW handlers
    │   ├── handlers.ts
    │   └── server.ts
    └── types/                    # TypeScript types
        └── audit.ts
```

## Scraper System

```
ScraperOrchestrator
    │
    ├── Resolves URL to Scraper
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                    IScraper Interface                        │
│         scrape(url) → AuctionLot                            │
└──────────────────────────┬──────────────────────────────────┘
                           │
    ┌──────────────────────┼──────────────────────┐
    │                      │                      │
    ▼                      ▼                      ▼
Heritage            CNG/Biddr/Agora           eBay
Scraper               Scrapers              Scraper
    │                      │                      │
    └──────────────────────┼──────────────────────┘
                           │
                           ▼
                    BasePlaywrightScraper
                    (Browser automation)
```

**Supported Auction Houses**: Heritage, CNG, Biddr (+ sub-houses), eBay, Agora

## Audit System

```
AuditEngine
    │
    ├── Runs Strategies
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│                    Audit Strategies                          │
├─────────────────────────────────────────────────────────────┤
│  AttributionStrategy  │ Validates issuer, portrait subject  │
│  PhysicsStrategy      │ Weight/diameter within tolerances   │
│  DateStrategy         │ Mint year vs reign dates            │
│  GradeStrategy        │ Grade vs expected for type          │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
                    AuditResult
                    (green/yellow/red)
```

## Security Considerations

- Single-user app (no authentication required)
- CORS configured for localhost origins
- File upload validation (type, size)
- SQL injection prevention via SQLAlchemy ORM
- Input validation via Pydantic schemas
- Foreign keys enforced via SQLite PRAGMA

## Database Considerations

- **Foreign Keys**: Enabled via SQLAlchemy event listener
- **Indexes**: On frequently queried columns (issuer, category, metal, dates)
- **Transactions**: Managed by `get_db()` dependency (auto-commit/rollback)
- **N+1 Prevention**: Eager loading with `selectinload` for relationships
