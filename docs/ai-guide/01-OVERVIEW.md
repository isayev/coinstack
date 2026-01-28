# CoinStack Overview

## What is CoinStack?

CoinStack is a **personal ancient coin collection management system** designed for numismatists (coin collectors/scholars). It's a single-user desktop/web application for cataloging Roman, Greek, Byzantine, and other ancient coins.

### Core Capabilities

1. **Collection Management** - CRUD operations for coins with rich metadata
2. **Reference Integration** - Lookups from OCRE, CRRO, RPC catalogs
3. **Auction Tracking** - Scrape and store auction data from multiple sources
4. **Data Enrichment** - LLM-powered field suggestions and catalog matching
5. **Quality Auditing** - Compare owned coins against auction records for discrepancies
6. **Import/Export** - Excel, CSV, URL parsing, NGC certificate lookup

### Supported Auction Sources

| Source | Website | Type |
|--------|---------|------|
| Heritage Auctions | https://coins.ha.com | Major auction house |
| CNG (Classical Numismatic Group) | https://cngcoins.com | Specialist ancient coins |
| Biddr | https://biddr.com | Aggregator (Savoca, etc.) |
| Roma Numismatics | https://romanumismatics.com | UK auction house |
| Agora Auctions | https://agoraauctions.com | Online auctions |
| eBay | https://www.ebay.com | Marketplace |
| VCoins | https://www.vcoins.com | Dealer marketplace |
| MA-Shops | https://www.ma-shops.com | Dealer marketplace |

### Reference Catalogs

| Catalog | Website | Coverage |
|---------|---------|----------|
| OCRE | http://numismatics.org/ocre/ | Roman Imperial (RIC) |
| CRRO | http://numismatics.org/crro/ | Roman Republican (Crawford) |
| RPC Online | https://rpc.ashmus.ox.ac.uk/ | Roman Provincial |
| Nomisma.org | http://nomisma.org/ | Linked numismatic data |

### Grading Services

| Service | Website | Description |
|---------|---------|-------------|
| NGC | https://www.ngccoin.com | Numismatic Guaranty Company |
| PCGS | https://www.pcgs.com | Professional Coin Grading Service |

## Tech Stack

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.12+ | Runtime |
| uv | Latest | Package manager & env (sync, run, lock); backend uses `uv run run_server.py` |
| FastAPI | Latest | Web framework |
| SQLAlchemy | 2.0 | ORM |
| Pydantic | 2.x | Data validation |
| SQLite | - | Database |
| Anthropic SDK | - | LLM integration |

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18 | UI framework |
| TypeScript | 5.x | Type safety |
| Vite | Latest | Build tool |
| TanStack Query | 5.x | Server state |
| Zustand | 4.x | Client state |
| Tailwind CSS | 3.x | Styling |
| shadcn/ui | - | Component library |

## Domain Terminology

### Coin Physical Terms

| Term | Definition |
|------|------------|
| **Obverse** | Front of coin, usually shows portrait |
| **Reverse** | Back of coin, shows design/scene |
| **Legend** | Text inscription around coin edge |
| **Exergue** | Area below main reverse design (often mint mark) |
| **Flan** | Blank metal disc before striking |
| **Die Axis** | Orientation between obverse/reverse (clock hours 1-12) |

### Coin Classification

| Term | Definition |
|------|------------|
| **Denomination** | Coin type by value (Denarius, Aureus, Sestertius, As) |
| **Metal** | Composition: Gold (AU), Silver (AR), Bronze (AE), Billon |
| **Category** | Era classification: Republic, Imperial, Provincial, Byzantine, Greek |
| **Issuing Authority** | Ruler/entity who issued the coin |
| **Portrait Subject** | Person depicted (may differ from issuer) |

### Reference Systems

| Code | Full Name | Covers |
|------|-----------|--------|
| **RIC** | Roman Imperial Coinage | Imperial coins (27 BC - 491 AD) |
| **RPC** | Roman Provincial Coinage | Provincial/Greek Imperial |
| **Crawford** | Roman Republican Coinage | Republican coins |
| **RSC** | Roman Silver Coins | Silver denominations |
| **BMCRE** | British Museum Catalog | Roman Empire |
| **Sear** | Roman Coins and Their Values | General reference |

### Grading

| Term | Definition |
|------|------------|
| **NGC/PCGS** | Third-party grading services |
| **Slab** | Encapsulated graded coin holder |
| **Grade** | Condition rating (Poor to MS/Mint State) |
| **Die Study** | Research linking coins from same dies |

### Collection Terms

| Term | Definition |
|------|------------|
| **Provenance** | Ownership history chain |
| **Countermark** | Official stamp added after minting |
| **Fouree** | Ancient counterfeit with base metal core |
| **Rarity** | How scarce: Common → Unique |

## Key Entities

### Core Data Model

```
Coin (central entity)
├── Basic Info: category, denomination, metal, series
├── Attribution: issuing_authority, portrait_subject, mint
├── Chronology: reign_start/end, mint_year_start/end
├── Physical: weight_g, diameter_mm, die_axis
├── Design: obverse/reverse legend, description, exergue
├── Grading: grade_service, grade, certification_number
├── Acquisition: date, price, source, url
├── Storage: holder_type, storage_location
└── Research: rarity, historical_significance, personal_notes

Related Entities:
├── Mint - Where coin was struck
├── CoinReference - Catalog citations (RIC I 207, Crawford 335/1)
├── CoinImage - Obverse/reverse photos
├── ProvenanceEvent - Ownership history entries
├── CoinTag - Custom tags
├── Countermark - Countermark stamps
└── AuctionData - Auction records linked to coins
```

### Enums Reference

**Category**
- `republic` - Roman Republic (509-27 BC)
- `imperial` - Roman Empire (27 BC - 476 AD)
- `provincial` - Roman Provincial/Greek Imperial
- `byzantine` - Byzantine Empire (330-1453 AD)
- `greek` - Ancient Greek city-states
- `other` - Other ancient coins

**Metal**
- `gold` (AU)
- `silver` (AR)
- `billon` (debased silver)
- `bronze` (AE)
- `orichalcum` (brass-like)
- `copper`

**Rarity**
- `common`
- `scarce`
- `rare`
- `very_rare`
- `extremely_rare`
- `unique`

**GradeService**
- `ngc` - NGC grading
- `pcgs` - PCGS grading
- `self` - Self-graded
- `dealer` - Dealer assessment

## Project Structure Map

```
coinstack/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app, CORS, routers
│   │   ├── config.py            # Settings (env vars)
│   │   ├── database.py          # SQLAlchemy engine, session
│   │   │
│   │   ├── models/              # SQLAlchemy ORM models
│   │   │   ├── coin.py          # Core Coin model + enums
│   │   │   ├── mint.py          # Mint locations
│   │   │   ├── reference.py     # CoinReference + ReferenceType
│   │   │   ├── image.py         # CoinImage with perceptual hash
│   │   │   ├── provenance.py    # ProvenanceEvent
│   │   │   ├── tag.py           # CoinTag
│   │   │   ├── countermark.py   # Countermark stamps
│   │   │   ├── auction_data.py  # AuctionData records
│   │   │   ├── audit_run.py     # Audit session tracking
│   │   │   ├── discrepancy.py   # Data conflicts
│   │   │   ├── enrichment.py    # Field suggestions
│   │   │   └── field_history.py # Change tracking
│   │   │
│   │   ├── schemas/             # Pydantic schemas
│   │   │   ├── coin.py          # Coin CRUD schemas
│   │   │   ├── auction.py       # Auction schemas
│   │   │   ├── audit.py         # Audit schemas
│   │   │   └── catalog.py       # Catalog lookup schemas
│   │   │
│   │   ├── routers/             # API endpoints
│   │   │   ├── coins.py         # /api/coins CRUD
│   │   │   ├── import_export.py # /api/import/*
│   │   │   ├── stats.py         # /api/stats
│   │   │   ├── settings.py      # /api/settings
│   │   │   ├── catalog.py       # /api/catalog/*
│   │   │   ├── auctions.py      # /api/auctions
│   │   │   ├── scrape.py        # /api/scrape/*
│   │   │   ├── audit.py         # /api/audit/*
│   │   │   ├── campaign.py      # /api/campaign/*
│   │   │   └── legend.py        # /api/legend/*
│   │   │
│   │   ├── crud/                # Database operations
│   │   │   ├── coin.py          # Coin CRUD
│   │   │   ├── auction.py       # Auction CRUD
│   │   │   └── audit.py         # Audit CRUD
│   │   │
│   │   └── services/            # Business logic
│   │       ├── excel_import.py
│   │       ├── reference_parser.py
│   │       ├── duplicate_detector.py
│   │       ├── ngc_connector.py
│   │       ├── legend_dictionary.py
│   │       ├── numismatic_synonyms.py
│   │       ├── diff_enricher.py
│   │       ├── llm_disambiguator.py
│   │       │
│   │       ├── catalogs/        # Catalog integrations
│   │       │   ├── base.py
│   │       │   ├── ocre.py      # OCRE (Imperial)
│   │       │   ├── crro.py      # CRRO (Republican)
│   │       │   ├── rpc.py       # RPC (Provincial)
│   │       │   └── registry.py
│   │       │
│   │       ├── scrapers/        # Auction scrapers
│   │       │   ├── base.py
│   │       │   ├── orchestrator.py
│   │       │   ├── heritage.py / heritage_rich/
│   │       │   ├── cng.py / cng_rich/
│   │       │   ├── biddr.py / biddr_rich/
│   │       │   ├── ebay.py / ebay_rich/
│   │       │   └── agora.py
│   │       │
│   │       └── audit/           # Audit services
│   │           ├── audit_service.py
│   │           ├── enrichment_service.py
│   │           ├── auto_merge.py
│   │           ├── comparator.py
│   │           ├── conflict_classifier.py
│   │           └── trust_config.py
│   │
│   └── data/
│       └── coinstack_v2.db      # SQLite database
│
└── frontend/
    └── src/
        ├── main.tsx             # Entry point
        ├── App.tsx              # Root component, routing
        ├── index.css            # Global styles, design tokens
        │
        ├── pages/               # Route pages
        │   ├── CollectionPage.tsx
        │   ├── CoinDetailPage.tsx
        │   ├── AddCoinPage.tsx
        │   ├── EditCoinPage.tsx
        │   ├── ImportPage.tsx
        │   ├── AuditPage.tsx
        │   ├── AuctionsPage.tsx
        │   ├── StatsPage.tsx
        │   └── SettingsPage.tsx
        │
        ├── components/
        │   ├── ui/              # shadcn/ui components
        │   ├── layout/          # AppShell, Header, Sidebar
        │   ├── coins/           # CoinCard, CoinTable, CoinForm
        │   ├── audit/           # Discrepancy, Enrichment cards
        │   ├── auctions/        # Auction components
        │   ├── import/          # Import workflow
        │   └── design-system/   # MetalBadge, GradeBadge, etc.
        │
        ├── hooks/               # TanStack Query hooks
        │   ├── useCoins.ts
        │   ├── useAudit.ts
        │   ├── useAuctions.ts
        │   ├── useCatalog.ts
        │   ├── useImport.ts
        │   └── useStats.ts
        │
        ├── stores/              # Zustand stores
        │   ├── uiStore.ts       # Sidebar, view mode
        │   ├── filterStore.ts   # Filters, pagination
        │   └── columnStore.ts   # Table columns
        │
        ├── types/               # TypeScript types
        │   ├── coin.ts
        │   └── audit.ts
        │
        └── lib/
            ├── api.ts           # Axios instance
            └── utils.ts         # Utilities
```

## Configuration Files

### Backend
- `backend/pyproject.toml` - Python dependencies, tool config
- `backend/.env` - Environment variables (API keys, DB path)

### Frontend
- `frontend/package.json` - Node dependencies, scripts
- `frontend/vite.config.ts` - Vite config (port, proxy)
- `frontend/tsconfig.json` - TypeScript config
- `frontend/tailwind.config.js` - Tailwind theme

### Cursor Rules
- `.cursor/rules/coding-standards.mdc` - Code style guidelines
- `.cursor/rules/project-context.mdc` - Domain context
- `.cursor/rules/git-authorship.mdc` - Git commit rules

---

**Next:** [02-ARCHITECTURE.md](02-ARCHITECTURE.md) - System architecture and diagrams
