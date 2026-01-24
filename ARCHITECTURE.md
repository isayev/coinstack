# CoinStack Architecture

## System Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│    Frontend     │────▶│    Backend      │────▶│    Database     │
│  React + Vite   │     │    FastAPI      │     │     SQLite      │
│  localhost:3000 │     │  localhost:8000 │     │  coinstack.db   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Data Model

### Core Entities

```
Coin (main entity)
├── id, created_at, updated_at
├── Classification: category, denomination, metal, series
├── People: issuing_authority, portrait_subject, status
├── Chronology: reign_start/end, mint_year_start/end
├── Physical: weight_g, diameter_mm, die_axis
├── Design: obverse/reverse legend, description, exergue
├── Grading: grade_service, grade, certification_number
├── Acquisition: date, price, source, url
├── Storage: holder_type, storage_location
└── Research: rarity, historical_significance, personal_notes

Relationships:
├── Mint (1:N) - Where coin was struck
├── CoinReference (1:N) - Catalog references (RIC, RPC, RSC)
├── CoinImage (1:N) - Obverse/reverse photos
├── ProvenanceEvent (1:N) - Ownership history
└── CoinTag (1:N) - Custom tags
```

### Enums

- **Category**: republic, imperial, provincial, byzantine, greek, other
- **Metal**: gold, silver, billon, bronze, orichalcum, copper
- **GradeService**: ngc, pcgs, self, dealer
- **Rarity**: common, scarce, rare, very_rare, extremely_rare, unique

## API Architecture

### Router Structure

```
/api
├── /coins          # CRUD operations
├── /stats          # Collection statistics
├── /import         # Excel/CSV import
└── /settings       # Backup, export, database info
```

### Request Flow

```
Request → Router → CRUD/Service → SQLAlchemy → SQLite
                                      ↓
Response ← Pydantic Schema ← Model ←──┘
```

## Frontend Architecture

### Component Hierarchy

```
App
├── ThemeProvider
├── QueryClientProvider
└── BrowserRouter
    └── AppShell
        ├── Header (search, add button, theme toggle)
        ├── Sidebar (navigation)
        ├── CommandPalette (Cmd+K)
        └── Routes
            ├── CollectionPage (grid/table)
            ├── CoinDetailPage
            ├── AddCoinPage
            ├── EditCoinPage
            ├── StatsPage
            ├── ImportPage
            └── SettingsPage
```

### State Management

- **Server State**: TanStack Query (coins, stats, settings)
- **UI State**: Zustand (sidebar, view mode, command palette)
- **Filter State**: Zustand with persistence (category, metal, etc.)

### Data Flow

```
Component → useQuery hook → api.ts → Backend API
                ↓
         Cache (TanStack Query)
                ↓
         Re-render on data change
```

## File Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app, middleware, routes
│   ├── config.py         # Settings (env vars)
│   ├── database.py       # SQLAlchemy engine, session
│   ├── models/           # SQLAlchemy ORM models
│   │   ├── coin.py
│   │   ├── mint.py
│   │   ├── reference.py
│   │   ├── image.py
│   │   ├── provenance.py
│   │   └── tag.py
│   ├── schemas/          # Pydantic schemas
│   │   └── coin.py
│   ├── routers/          # API endpoints
│   │   ├── coins.py
│   │   ├── stats.py
│   │   ├── import_export.py
│   │   └── settings.py
│   ├── crud/             # Database operations
│   │   └── coin.py
│   └── services/         # Business logic
│       └── excel_import.py
└── data/
    └── coinstack.db

frontend/
└── src/
    ├── main.tsx          # Entry point
    ├── App.tsx           # Root component, routing
    ├── components/
    │   ├── ui/           # shadcn/ui components
    │   ├── layout/       # App shell components
    │   └── coins/        # Coin-specific components
    ├── pages/            # Route pages
    ├── hooks/            # React Query hooks
    ├── stores/           # Zustand stores
    ├── types/            # TypeScript interfaces
    └── lib/              # Utilities (api, cn)
```

## Security Considerations

- Single-user app (no authentication required)
- CORS configured for localhost origins
- File upload validation (type, size)
- SQL injection prevention via SQLAlchemy ORM
- Input validation via Pydantic schemas
