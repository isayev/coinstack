# CoinStack

A personal ancient coin collection management system for numismatists, featuring catalog integration, intelligent data enrichment, and comprehensive collection analytics.

---

## 🚨 For Developers & AI Assistants

**BEFORE making ANY code changes, read:**
- **[DOCUMENTATION_RULES.md](DOCUMENTATION_RULES.md)** - MANDATORY documentation sync protocol
- **[docs/ai-guide/README.md](docs/ai-guide/README.md)** - Complete developer guide index
- **[CLAUDE.md](CLAUDE.md)** - Project instructions for Claude Code

**Key Rule**: All frontend/backend changes MUST consult `design/` specs and `docs/ai-guide/` BEFORE implementation, and update `docs/ai-guide/` AFTER changes. Documentation is the authoritative source of truth.

---

## Features

### Collection Management
- **Full Metadata Cataloging**: Denomination, metal, ruler, dates (BC/AD), legends, physical attributes
- **Extended Data Model**: Die axis, die studies, countermarks, auction history, price tracking
- **Reference System**: Type-centric reference tracking (RIC, RPC, Crawford, Sear, BMC, etc.)
- **Provenance Tracking**: Auction records, dealer history, price history

### Views & Navigation
- **Grid & Table Views**: Visual grid or sortable data table
- **Advanced Filtering**: Category, metal, ruler, mint, date range, rarity, grade, storage location
- **Sorting Options**: Year, name, weight, rarity (with proper BC/AD chronological ordering)
- **Navigation**: Previous/next coin arrows on detail pages

### Data Enrichment
- **Catalog Integration**: OCRE (RIC), CRRO (Crawford), RPC lookups
- **Legend Expansion**: Dictionary-based + LLM-powered abbreviation expansion (IMP → Imperator)
- **Bulk Enrichment**: Queue-based batch processing with conflict resolution
- **Compare Drawer**: Side-by-side view of local vs catalog data

### Import/Export
- **Excel/CSV Import**: Intelligent parsing with text normalization
  - BC/AD date handling (negative years for BC)
  - Abbreviated year expansion (159-60 → 159-160)
  - Reference string parsing (RIC, RPC, Crawford, Sear, BMC, Cohen, etc.)
  - Greek text and special character preservation
- **Export**: CSV export, database backup
- **Text Normalization**: Non-breaking spaces, special dashes, multiple spaces cleaned

### Analytics
- **Statistics Dashboard**: Collection value, distribution charts
- **Category/Metal Breakdown**: Visual pie charts with all enum types
- **Top Rulers**: Bar chart of most represented rulers
- **Weight Tracking**: Total collection weight by metal

### UI/UX
- **Image Zoom**: Pan, zoom, rotate coin images
- **Dark/Light Theme**: System-aware theming
- **Responsive Design**: Modern shadcn/ui components

## Tech Stack

### Backend
- Python 3.12+
- FastAPI
- SQLAlchemy 2.0 (ORM)
- Pydantic 2.x (validation)
- SQLite (database)
- Anthropic SDK (Claude LLM for disambiguation)
- httpx (external API calls)
- openpyxl (Excel parsing)

### Frontend
- React 18
- TypeScript 5.x
- Vite (build tool)
- TanStack Query (data fetching)
- Zustand (state management)
- Tailwind CSS + shadcn/ui (styling)
- Recharts (charts)
- React Hook Form + Zod (forms)

## Data Model

### Core Entities
- **Coin**: Extended with `is_circa`, `is_test_cut`, `die_axis`, `die_study_*`, `sub_category`, `estimated_value_usd`
- **CoinReference**: Links coins to ReferenceType (type-centric design)
- **ReferenceType**: Shared catalog type info with external lookups
- **ProvenanceEvent**: Auction details, hammer price, buyer's premium
- **Countermark**: Provincial coin countermark tracking
- **AuctionData**: Market data from auction houses
- **PriceHistory**: Price trends by reference type

### Enums
- **Category**: imperial, republic, provincial, byzantine, greek, celtic, judaean, migration, pseudo_roman, other
- **Metal**: gold, silver, bronze, copper, billon, electrum, orichalcum, potin, lead, ae, uncertain

## Project Structure

```
coinstack/
├── backend/
│   ├── app/
│   │   ├── models/          # SQLAlchemy ORM models
│   │   │   ├── coin.py      # Coin, Category, Metal enums
│   │   │   ├── reference.py # CoinReference
│   │   │   ├── reference_type.py # ReferenceType, ReferenceMatchAttempt
│   │   │   ├── countermark.py    # Countermark model
│   │   │   ├── auction_data.py   # AuctionData model
│   │   │   └── price_history.py  # PriceHistory model
│   │   ├── schemas/         # Pydantic schemas
│   │   ├── routers/         # API endpoints
│   │   │   ├── coins.py     # CRUD + navigation
│   │   │   ├── catalog.py   # Catalog lookup/enrich
│   │   │   ├── legend.py    # Legend expansion
│   │   │   └── stats.py     # Analytics
│   │   ├── services/        # Business logic
│   │   │   ├── excel_import.py      # Import with normalization
│   │   │   ├── legend_dictionary.py # 50+ abbreviations
│   │   │   ├── numismatic_synonyms.py # Dynasty/grade mappings
│   │   │   ├── reference_parser.py  # Reference string parsing
│   │   │   ├── diff_enricher.py     # Catalog diff computation
│   │   │   ├── llm_disambiguator.py # Claude disambiguation
│   │   │   └── catalogs/            # OCRE, CRRO, RPC services
│   │   └── crud/            # Database operations
│   ├── data/                # SQLite database
│   └── uploads/             # Uploaded images
├── frontend/
│   └── src/
│       ├── components/
│       │   ├── coins/
│       │   │   ├── CoinCard.tsx       # Grid card with badges
│       │   │   ├── CoinFilters.tsx    # Advanced filter panel
│       │   │   ├── CoinForm.tsx       # Add/Edit form
│       │   │   ├── CompareDrawer.tsx  # Catalog comparison
│       │   │   ├── ImageZoom.tsx      # Image viewer
│       │   │   ├── LegendInput.tsx    # Legend expansion input
│       │   │   └── ReferenceSuggest.tsx # Reference autocomplete
│       │   └── ui/           # shadcn/ui components
│       ├── pages/
│       │   ├── CollectionPage.tsx  # Grid/table with filters
│       │   ├── CoinDetailPage.tsx  # Full detail with tabs
│       │   ├── BulkEnrichPage.tsx  # Batch enrichment
│       │   └── StatsPage.tsx       # Analytics dashboard
│       ├── hooks/            # TanStack Query hooks
│       ├── stores/           # Zustand state (filters)
│       └── types/            # TypeScript definitions
└── original-data/            # Source Excel files
```

## Getting Started

### Prerequisites
- Python 3.12+
- Node.js 18+
- npm or yarn

### Backend Setup

```bash
cd backend
pip install -e .
# Or manually:
pip install fastapi uvicorn sqlalchemy pydantic pydantic-settings alembic python-multipart openpyxl anthropic httpx python-dateutil

python -m uvicorn app.main:app --reload --port 8000
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

### Import Collection

```bash
# Via API
curl -X POST "http://localhost:8000/api/import/collection" \
  -F "file=@collection.xlsx"

# Or use the Import page in the UI
```

### Access
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## API Endpoints

### Core CRUD
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/coins` | GET | List coins with pagination/filters/sorting |
| `/api/coins` | POST | Create new coin |
| `/api/coins/{id}` | GET | Get coin detail |
| `/api/coins/{id}` | PUT | Update coin |
| `/api/coins/{id}` | DELETE | Delete coin |
| `/api/coins/{id}/navigation` | GET | Get prev/next coin IDs |

### Catalog Integration
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/catalog/lookup` | POST | Look up reference in external catalog |
| `/api/catalog/enrich/{coin_id}` | POST | Enrich coin from catalog |
| `/api/catalog/bulk-enrich` | POST | Start bulk enrichment job |
| `/api/catalog/job/{job_id}` | GET | Check bulk job status |

### Legend & Search
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/legend/expand` | POST | Expand legend abbreviations |
| `/api/legend/lookup/{abbr}` | GET | Look up single abbreviation |
| `/api/legend/search` | GET | Search with synonym expansion |

### Analytics & Settings
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/stats` | GET | Collection statistics |
| `/api/import/collection` | POST | Import from Excel/CSV |
| `/api/settings/backup` | GET | Download database backup |
| `/api/settings/export-csv` | GET | Export to CSV |

## Excel Import Format

Expected columns (flexible naming):
- `Ruler Issuer` - Issuing authority
- `Coin type` - Denomination
- `Category` - Roman Imperial/Provincial/Republic
- `Composition` - Metal (Silver, Gold, Bronze, etc.)
- `Minted` - Mint date (e.g., "2 BC-AD 4", "96 BC", "AD 140/141")
- `Ruled` - Reign dates
- `Reference` - Catalog references (e.g., "RIC I 207; Crawford 335/1c")
- `Obverse` / `Reverse` - Design descriptions with legends
- `Weight` / `Diameter` - Physical measurements
- `Condition` / `NGC Grade` - Grading info
- `Mint` - Mint location
- `Amount Paid` - Acquisition price
- `Source` / `Link` - Provenance info

### Supported Reference Formats
- RIC: `RIC I 207`, `RIC II.1 756`, `RIC IV.III (Trajan Decius) 58b`
- RPC: `RPC I 1701a`, `RPC V.3 1234`
- Crawford: `Crawford 335/1c`
- Sear: `Sear 8677`, `SEAR II 5722`, `SRCV 11967`
- BMC: `BMC 837`, `BMCRE 227`
- RSC: `RSC 966`
- Cohen: `Cohen 161`, `Coh. 84`
- Sydenham: `Sydenham 611`
- SNG: `SNG Cop 281-282`
- And more...

## Changelog

### v0.2.0 (Current)
- Type-centric reference system with ReferenceType table
- Catalog integration (OCRE, CRRO, RPC)
- Legend expansion with dictionary + LLM fallback
- Bulk enrichment with job queue
- Advanced filtering (year range, circa, test cut, rarity)
- Proper BC/AD date sorting
- Text normalization preserving Greek
- Image zoom component
- Navigation arrows on detail pages
- Extended enums (Metal, Category)
- Countermark, AuctionData, PriceHistory models

### v0.1.0
- Core data model (Coin, Mint, Reference, Image, Provenance)
- Collection grid/table views with filtering
- Coin detail pages with tabs
- Add/Edit coin forms
- Statistics dashboard with charts
- Excel/CSV import wizard
- Settings page (backup, export, theme)
- Dark/light theme support

## License

Private project - All rights reserved.

## Author

isayev (olexandr@olexandrisayev.com)
