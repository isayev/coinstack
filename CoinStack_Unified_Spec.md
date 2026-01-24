# CoinStack — Unified Engineering Specification

**Version**: 2.0  
**Last Updated**: January 2025  
**Author**: Synthesized from dual architecture review

---

## Executive Summary

A personal web application for managing an ancient coin collection (~110+ coins, primarily Roman Imperial) with structured relational data, LLM-assisted cataloging, and intelligent search. Built as a modern, responsive SPA with native app-like UX.

**Stack Decision**: 
- **Backend**: Python/FastAPI/SQLite — ecosystem alignment, LLM integration, operational simplicity
- **Frontend**: React 18 + TypeScript + Vite — modern SPA with rich interactivity, shadcn/ui components

---

## 1. Architecture Overview

```
coinstack/
├── frontend/                   # React SPA
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── index.css
│   │   │
│   │   ├── components/
│   │   │   ├── ui/             # shadcn/ui components
│   │   │   │   ├── button.tsx
│   │   │   │   ├── card.tsx
│   │   │   │   ├── dialog.tsx
│   │   │   │   ├── input.tsx
│   │   │   │   ├── select.tsx
│   │   │   │   ├── table.tsx
│   │   │   │   ├── tabs.tsx
│   │   │   │   └── ...
│   │   │   │
│   │   │   ├── coins/
│   │   │   │   ├── CoinCard.tsx
│   │   │   │   ├── CoinDetail.tsx
│   │   │   │   ├── CoinForm.tsx
│   │   │   │   ├── CoinGrid.tsx
│   │   │   │   ├── CoinTable.tsx
│   │   │   │   ├── CoinFilters.tsx
│   │   │   │   └── CoinImageGallery.tsx
│   │   │   │
│   │   │   ├── references/
│   │   │   │   ├── ReferenceList.tsx
│   │   │   │   └── ReferenceForm.tsx
│   │   │   │
│   │   │   ├── provenance/
│   │   │   │   ├── ProvenanceTimeline.tsx
│   │   │   │   └── ProvenanceForm.tsx
│   │   │   │
│   │   │   ├── llm/
│   │   │   │   ├── ParseListingDialog.tsx
│   │   │   │   ├── NaturalSearchBar.tsx
│   │   │   │   ├── CoinIdentifier.tsx
│   │   │   │   └── LegendExpander.tsx
│   │   │   │
│   │   │   ├── import/
│   │   │   │   ├── ImportWizard.tsx
│   │   │   │   └── ColumnMapper.tsx
│   │   │   │
│   │   │   ├── stats/
│   │   │   │   ├── Dashboard.tsx
│   │   │   │   ├── ValueChart.tsx
│   │   │   │   └── CompositionCharts.tsx
│   │   │   │
│   │   │   └── layout/
│   │   │       ├── Header.tsx
│   │   │       ├── Sidebar.tsx
│   │   │       ├── CommandPalette.tsx
│   │   │       └── ThemeToggle.tsx
│   │   │
│   │   ├── pages/
│   │   │   ├── CollectionPage.tsx
│   │   │   ├── CoinDetailPage.tsx
│   │   │   ├── AddCoinPage.tsx
│   │   │   ├── EditCoinPage.tsx
│   │   │   ├── ImportPage.tsx
│   │   │   ├── StatsPage.tsx
│   │   │   └── SettingsPage.tsx
│   │   │
│   │   ├── hooks/
│   │   │   ├── useCoins.ts
│   │   │   ├── useCoin.ts
│   │   │   ├── useCreateCoin.ts
│   │   │   ├── useUpdateCoin.ts
│   │   │   ├── useDeleteCoin.ts
│   │   │   ├── useReferences.ts
│   │   │   ├── useProvenance.ts
│   │   │   ├── useImages.ts
│   │   │   ├── useSearch.ts
│   │   │   ├── useLLM.ts
│   │   │   ├── useStats.ts
│   │   │   └── useVocabularies.ts
│   │   │
│   │   ├── lib/
│   │   │   ├── api.ts            # Axios/fetch client
│   │   │   ├── utils.ts          # cn(), formatters
│   │   │   ├── constants.ts
│   │   │   └── validators.ts     # Zod schemas
│   │   │
│   │   ├── stores/
│   │   │   ├── filterStore.ts    # Zustand filter state
│   │   │   ├── uiStore.ts        # UI state (modals, sidebar)
│   │   │   └── selectionStore.ts # Bulk selection
│   │   │
│   │   └── types/
│   │       ├── coin.ts
│   │       ├── reference.ts
│   │       ├── provenance.ts
│   │       └── api.ts
│   │
│   ├── public/
│   ├── index.html
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   ├── tsconfig.json
│   └── package.json
│
├── backend/                    # FastAPI
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI app factory
│   │   ├── config.py           # Settings via pydantic-settings
│   │   ├── database.py         # SQLAlchemy engine + session
│   │   │
│   │   ├── models/             # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── coin.py
│   │   │   ├── reference.py
│   │   │   ├── provenance.py
│   │   │   ├── image.py
│   │   │   └── mint.py
│   │   │
│   │   ├── schemas/            # Pydantic request/response
│   │   │   ├── __init__.py
│   │   │   ├── coin.py
│   │   │   ├── reference.py
│   │   │   ├── provenance.py
│   │   │   ├── search.py
│   │   │   └── llm.py
│   │   │
│   │   ├── crud/               # Database operations
│   │   │   ├── __init__.py
│   │   │   ├── coin.py
│   │   │   ├── reference.py
│   │   │   ├── provenance.py
│   │   │   └── stats.py
│   │   │
│   │   ├── routers/            # API endpoints
│   │   │   ├── __init__.py
│   │   │   ├── coins.py
│   │   │   ├── references.py
│   │   │   ├── provenance.py
│   │   │   ├── images.py
│   │   │   ├── search.py
│   │   │   ├── llm.py
│   │   │   ├── import_export.py
│   │   │   └── stats.py
│   │   │
│   │   └── services/           # Business logic
│   │       ├── __init__.py
│   │       ├── claude.py       # LLM integration
│   │       ├── csv_import.py
│   │       ├── image_processor.py
│   │       └── search.py
│   │
│   ├── data/
│   │   ├── vocabularies/
│   │   │   ├── rulers.json
│   │   │   ├── mints.json
│   │   │   ├── denominations.json
│   │   │   └── references.json
│   │   └── imports/
│   │       └── collection-v1.csv
│   │
│   ├── tests/
│   │   ├── conftest.py
│   │   ├── test_schemas.py
│   │   ├── test_crud.py
│   │   ├── test_api.py
│   │   ├── test_import.py
│   │   ├── test_llm.py
│   │   └── integration/
│   │
│   ├── alembic/
│   │   ├── versions/
│   │   └── env.py
│   │
│   ├── pyproject.toml
│   └── Dockerfile
│
├── docker-compose.yml
├── Makefile
└── README.md
```

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Browser                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                      React SPA (Vite + TypeScript)                     │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────────┐  │  │
│  │  │  TanStack   │ │   Zustand   │ │  React      │ │   shadcn/ui     │  │  │
│  │  │   Query     │ │   Stores    │ │  Router     │ │   + Tailwind    │  │  │
│  │  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      │ REST API + SSE (LLM streaming)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FastAPI Backend                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │   REST Routes   │  │  Claude Service │  │    Background Tasks         │  │
│  │   /api/coins    │  │  (Anthropic SDK)│  │    (image processing)       │  │
│  │   /api/llm      │  │                 │  │                             │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            Data Layer                                        │
│  ┌───────────────────────┐  ┌────────────────────┐  ┌───────────────────┐   │
│  │   SQLite Database     │  │   Local Filesystem │  │  Vocabularies     │   │
│  │   (SQLAlchemy 2.0)    │  │   (coin images)    │  │  (JSON files)     │   │
│  └───────────────────────┘  └────────────────────┘  └───────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Technology Stack

### Backend

| Layer | Technology | Version | Rationale |
|-------|------------|---------|-----------|
| Runtime | Python | 3.12+ | Type hints, performance |
| Framework | FastAPI | 0.115+ | Auto-docs, async, Pydantic integration |
| ORM | SQLAlchemy | 2.0+ | Mature, typed, flexible |
| Validation | Pydantic | 2.9+ | Excellent error messages |
| Database | SQLite | 3.40+ | Zero-config, portable, sufficient for 10K+ coins |
| Migrations | Alembic | 1.13+ | Schema versioning |
| LLM | Claude API | claude-sonnet-4-20250514 | Structured extraction, vision |
| Testing | pytest | 8.3+ | Fixtures, coverage |
| Linting | Ruff + mypy | Latest | Fast, comprehensive |
| Package Mgmt | uv | Latest | Fast resolver |

### Frontend

| Layer | Technology | Version | Rationale |
|-------|------------|---------|-----------|
| Framework | React | 18.3+ | Mature ecosystem, concurrent features |
| Language | TypeScript | 5.4+ | Type safety, excellent DX |
| Build | Vite | 5.x | Fast HMR, ESM-native |
| Routing | React Router | 6.x | Nested routes, data loading |
| Data Fetching | TanStack Query | 5.x | Caching, mutations, optimistic updates |
| State | Zustand | 4.x | Minimal, TypeScript-first |
| UI Components | shadcn/ui | Latest | Composable, accessible, customizable |
| Styling | Tailwind CSS | 3.4+ | Utility-first, design system |
| Forms | React Hook Form | 7.x | Performance, validation |
| Validation | Zod | 3.x | TypeScript-first schemas |
| Charts | Recharts | 2.x | Declarative, responsive |
| Icons | Lucide React | Latest | Consistent, tree-shakeable |
| Date Handling | date-fns | 3.x | Immutable, modular |

### Infrastructure

| Layer | Technology | Rationale |
|-------|------------|-----------|
| Containerization | Docker | Reproducible builds |
| Reverse Proxy | Caddy or nginx | Simple HTTPS, static serving |
| CI/CD | GitHub Actions | Native integration |

---

## 3. Data Model

### 3.1 Entity Relationship Diagram

```
┌─────────────┐       ┌─────────────────┐       ┌─────────────────┐
│    Mint     │       │      Coin       │       │  CoinReference  │
├─────────────┤       ├─────────────────┤       ├─────────────────┤
│ id          │◄──────│ mint_id (FK)    │───────│ coin_id (FK)    │
│ name        │       │ id              │       │ id              │
│ province    │       │ category        │       │ system          │
│ modern_loc  │       │ denomination    │       │ volume          │
│ latitude    │       │ metal           │       │ number          │
│ longitude   │       │ ...             │       │ is_primary      │
└─────────────┘       └────────┬────────┘       └─────────────────┘
                               │
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
   ┌─────────────────┐  ┌─────────────┐  ┌─────────────┐
   │ ProvenanceEvent │  │  CoinImage  │  │  CoinTag    │
   ├─────────────────┤  ├─────────────┤  ├─────────────┤
   │ coin_id (FK)    │  │ coin_id (FK)│  │ coin_id (FK)│
   │ event_type      │  │ image_type  │  │ tag         │
   │ event_date      │  │ file_path   │  └─────────────┘
   │ auction_house   │  │ is_primary  │
   │ price           │  └─────────────┘
   │ ...             │
   └─────────────────┘
```

### 3.2 SQLAlchemy Models

#### Coin (Primary Entity)

```python
# app/models/coin.py
from sqlalchemy import (
    Column, Integer, String, Numeric, Date, Boolean, 
    ForeignKey, Enum, Text, JSON, DateTime
)
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.database import Base


class Category(enum.Enum):
    REPUBLIC = "republic"
    IMPERIAL = "imperial"
    PROVINCIAL = "provincial"
    BYZANTINE = "byzantine"
    GREEK = "greek"
    OTHER = "other"


class Metal(enum.Enum):
    GOLD = "gold"
    SILVER = "silver"
    BILLON = "billon"
    BRONZE = "bronze"
    ORICHALCUM = "orichalcum"
    COPPER = "copper"


class DatingCertainty(enum.Enum):
    EXACT = "exact"
    NARROW = "narrow"
    BROAD = "broad"
    UNKNOWN = "unknown"


class GradeService(enum.Enum):
    NGC = "ngc"
    PCGS = "pcgs"
    SELF = "self"
    DEALER = "dealer"


class HolderType(enum.Enum):
    NGC_SLAB = "ngc_slab"
    PCGS_SLAB = "pcgs_slab"
    FLIP = "flip"
    CAPSULE = "capsule"
    TRAY = "tray"
    RAW = "raw"


class Rarity(enum.Enum):
    COMMON = "common"
    SCARCE = "scarce"
    RARE = "rare"
    VERY_RARE = "very_rare"
    EXTREMELY_RARE = "extremely_rare"
    UNIQUE = "unique"


class Coin(Base):
    __tablename__ = "coins"
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # === Classification ===
    category = Column(Enum(Category), nullable=False, index=True)
    denomination = Column(String(50), nullable=False, index=True)
    metal = Column(Enum(Metal), nullable=False, index=True)
    series = Column(String(100))  # "Travel Series", "Consecratio", etc.
    
    # === People ===
    issuing_authority = Column(String(100), nullable=False, index=True)  # Who issued it
    portrait_subject = Column(String(100), index=True)  # Who's depicted
    status = Column(String(50))  # "as Caesar", "as Augustus", "Divus"
    
    # === Chronology ===
    reign_start = Column(Integer)  # Year (negative for BC)
    reign_end = Column(Integer)
    mint_year_start = Column(Integer)
    mint_year_end = Column(Integer)
    dating_certainty = Column(Enum(DatingCertainty), default=DatingCertainty.BROAD)
    dating_notes = Column(String(255))
    
    # === Physical Attributes ===
    weight_g = Column(Numeric(6, 2))
    diameter_mm = Column(Numeric(5, 2))
    diameter_min_mm = Column(Numeric(5, 2))  # For irregular flans
    thickness_mm = Column(Numeric(4, 2))
    die_axis = Column(Integer)  # Clock hours 1-12
    
    # === Design: Obverse ===
    obverse_legend = Column(String(255))
    obverse_legend_expanded = Column(Text)
    obverse_description = Column(Text)
    obverse_symbols = Column(String(255))  # Control marks, etc.
    
    # === Design: Reverse ===
    reverse_legend = Column(String(255))
    reverse_legend_expanded = Column(Text)
    reverse_description = Column(Text)
    reverse_symbols = Column(String(255))
    exergue = Column(String(100))
    
    # === Mint ===
    mint_id = Column(Integer, ForeignKey("mints.id"))
    mint = relationship("Mint", back_populates="coins")
    officina = Column(String(20))  # Workshop letter/number
    script = Column(String(20))  # Latin, Greek
    
    # === Grading ===
    grade_service = Column(Enum(GradeService))
    grade = Column(String(50))
    strike_quality = Column(Integer)  # 1-5
    surface_quality = Column(Integer)  # 1-5
    certification_number = Column(String(50))
    surface_issues = Column(JSON)  # ["scratched", "cleaned"]
    eye_appeal = Column(String(50))
    toning_description = Column(String(255))
    style_notes = Column(String(255))  # "Fine style", "Provincial"
    
    # === Acquisition ===
    acquisition_date = Column(Date)
    acquisition_price = Column(Numeric(10, 2))
    acquisition_currency = Column(String(3), default="USD")
    acquisition_source = Column(String(100))  # Heritage, CNG, eBay
    acquisition_url = Column(String(500))
    
    # === Valuation ===
    estimate_low = Column(Numeric(10, 2))
    estimate_high = Column(Numeric(10, 2))
    estimate_date = Column(Date)
    insured_value = Column(Numeric(10, 2))
    
    # === Storage ===
    holder_type = Column(Enum(HolderType))
    storage_location = Column(String(50))  # "SlabBox1", "Velv2-3-1"
    for_sale = Column(Boolean, default=False)
    asking_price = Column(Numeric(10, 2))
    
    # === Research ===
    rarity = Column(Enum(Rarity))
    rarity_notes = Column(String(255))
    historical_significance = Column(Text)
    die_match_notes = Column(Text)
    personal_notes = Column(Text)
    
    # === LLM Enrichment ===
    llm_enriched = Column(JSON)  # Cached LLM suggestions
    llm_enriched_at = Column(DateTime)
    
    # === Relationships ===
    references = relationship("CoinReference", back_populates="coin", cascade="all, delete-orphan")
    provenance_events = relationship("ProvenanceEvent", back_populates="coin", cascade="all, delete-orphan", order_by="ProvenanceEvent.sort_order")
    images = relationship("CoinImage", back_populates="coin", cascade="all, delete-orphan")
    tags = relationship("CoinTag", back_populates="coin", cascade="all, delete-orphan")
```

#### Supporting Models

```python
# app/models/mint.py
class Mint(Base):
    __tablename__ = "mints"
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    province = Column(String(100))
    modern_location = Column(String(100))
    latitude = Column(Numeric(9, 6))
    longitude = Column(Numeric(9, 6))
    
    coins = relationship("Coin", back_populates="mint")


# app/models/reference.py
class ReferenceSystem(enum.Enum):
    RIC = "ric"
    CRAWFORD = "crawford"
    RPC = "rpc"
    RSC = "rsc"
    BMCRE = "bmcre"
    SEAR = "sear"
    SYDENHAM = "sydenham"
    OTHER = "other"


class CoinReference(Base):
    __tablename__ = "coin_references"
    
    id = Column(Integer, primary_key=True)
    coin_id = Column(Integer, ForeignKey("coins.id", ondelete="CASCADE"), nullable=False, index=True)
    
    system = Column(Enum(ReferenceSystem), nullable=False)
    volume = Column(String(20))  # "III", "IV.1"
    number = Column(String(50), nullable=False)  # "207", "335/1c"
    is_primary = Column(Boolean, default=False)
    plate_coin = Column(Boolean, default=False)
    notes = Column(String(255))
    
    coin = relationship("Coin", back_populates="references")


# app/models/provenance.py
class ProvenanceType(enum.Enum):
    AUCTION = "auction"
    PRIVATE_SALE = "private_sale"
    DEALER = "dealer"
    FIND = "find"
    INHERITANCE = "inheritance"
    GIFT = "gift"


class ProvenanceEvent(Base):
    __tablename__ = "provenance_events"
    
    id = Column(Integer, primary_key=True)
    coin_id = Column(Integer, ForeignKey("coins.id", ondelete="CASCADE"), nullable=False, index=True)
    
    event_type = Column(Enum(ProvenanceType), nullable=False)
    event_date = Column(Date)
    auction_house = Column(String(100))
    sale_name = Column(String(100))  # "Auction 3125"
    lot_number = Column(String(20))
    collection_name = Column(String(100))  # "Peh Family Collection"
    price = Column(Numeric(10, 2))
    currency = Column(String(3))
    url = Column(String(500))
    notes = Column(Text)
    sort_order = Column(Integer, default=0)  # For ordering chain
    
    coin = relationship("Coin", back_populates="provenance_events")


# app/models/image.py
class ImageType(enum.Enum):
    OBVERSE = "obverse"
    REVERSE = "reverse"
    EDGE = "edge"
    SLAB = "slab"
    DETAIL = "detail"
    COMBINED = "combined"


class CoinImage(Base):
    __tablename__ = "coin_images"
    
    id = Column(Integer, primary_key=True)
    coin_id = Column(Integer, ForeignKey("coins.id", ondelete="CASCADE"), nullable=False, index=True)
    
    image_type = Column(Enum(ImageType), nullable=False)
    file_path = Column(String(255), nullable=False)
    file_name = Column(String(100))
    mime_type = Column(String(50))
    size_bytes = Column(Integer)
    width = Column(Integer)
    height = Column(Integer)
    is_primary = Column(Boolean, default=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    coin = relationship("Coin", back_populates="images")


# app/models/tag.py
class CoinTag(Base):
    __tablename__ = "coin_tags"
    
    id = Column(Integer, primary_key=True)
    coin_id = Column(Integer, ForeignKey("coins.id", ondelete="CASCADE"), nullable=False, index=True)
    tag = Column(String(50), nullable=False, index=True)
    
    coin = relationship("Coin", back_populates="tags")
    
    __table_args__ = (
        # Prevent duplicate tags per coin
        {"sqlite_autoincrement": True},
    )
```

---

## 4. API Specification

### 4.1 Endpoints

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| **Coins** |
| GET | `/api/coins` | List coins (paginated, filtered) | — |
| POST | `/api/coins` | Create coin | — |
| GET | `/api/coins/{id}` | Get coin detail with relations | — |
| PUT | `/api/coins/{id}` | Update coin | — |
| DELETE | `/api/coins/{id}` | Delete coin | — |
| POST | `/api/coins/bulk` | Bulk update (storage, tags) | — |
| **References** |
| POST | `/api/coins/{id}/references` | Add reference | — |
| DELETE | `/api/coins/{id}/references/{ref_id}` | Remove reference | — |
| **Provenance** |
| POST | `/api/coins/{id}/provenance` | Add provenance event | — |
| PUT | `/api/coins/{id}/provenance/{event_id}` | Update event | — |
| DELETE | `/api/coins/{id}/provenance/{event_id}` | Remove event | — |
| **Images** |
| POST | `/api/coins/{id}/images` | Upload image | — |
| DELETE | `/api/coins/{id}/images/{image_id}` | Remove image | — |
| PUT | `/api/coins/{id}/images/{image_id}/primary` | Set as primary | — |
| **Search** |
| GET | `/api/search` | Faceted search | — |
| POST | `/api/search/query` | Natural language search | — |
| **LLM** |
| POST | `/api/llm/parse-listing` | Extract fields from auction text | — |
| POST | `/api/llm/identify` | Identify coin from image | — |
| POST | `/api/llm/expand-legend` | Expand abbreviated legend | — |
| POST | `/api/coins/{id}/enrich` | LLM enrichment for coin | — |
| **Import/Export** |
| POST | `/api/import/csv` | Import CSV with mapping | — |
| GET | `/api/export/csv` | Export collection | — |
| GET | `/api/export/json` | Export as JSON | — |
| **Stats** |
| GET | `/api/stats/overview` | Collection summary | — |
| GET | `/api/stats/by-ruler` | Breakdown by ruler | — |
| GET | `/api/stats/by-period` | Breakdown by period | — |
| GET | `/api/stats/by-metal` | Breakdown by metal | — |
| GET | `/api/stats/value-history` | Value over time | — |
| **Vocabularies** |
| GET | `/api/vocab/rulers` | Ruler autocomplete | — |
| GET | `/api/vocab/mints` | Mint autocomplete | — |
| GET | `/api/vocab/denominations` | Denomination list | — |

### 4.2 Query Parameters for `/api/coins`

```
GET /api/coins?
  page=1&
  per_page=20&
  sort=acquisition_date&
  order=desc&
  # Filters
  category=imperial&
  metal=silver&
  issuing_authority=Augustus&
  mint=Rome&
  denomination=Denarius&
  reign_start_gte=-27&
  reign_end_lte=14&
  acquisition_price_gte=100&
  acquisition_price_lte=500&
  grade_service=ngc&
  for_sale=true&
  storage_location=SlabBox1&
  tag=laureate
```

### 4.3 Response Schemas

```python
# app/schemas/coin.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List
from datetime import date, datetime
from decimal import Decimal

from app.models.coin import Category, Metal, DatingCertainty, GradeService, HolderType, Rarity


class CoinReferenceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    system: str
    volume: Optional[str]
    number: str
    is_primary: bool
    plate_coin: bool


class ProvenanceEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    event_type: str
    event_date: Optional[date]
    auction_house: Optional[str]
    sale_name: Optional[str]
    lot_number: Optional[str]
    collection_name: Optional[str]
    price: Optional[Decimal]
    currency: Optional[str]
    url: Optional[str]
    notes: Optional[str]


class CoinImageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    image_type: str
    file_path: str
    is_primary: bool


class CoinListItem(BaseModel):
    """Compact representation for list views."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    category: Category
    denomination: str
    metal: Metal
    issuing_authority: str
    portrait_subject: Optional[str]
    mint_name: Optional[str]
    grade: Optional[str]
    acquisition_price: Optional[Decimal]
    storage_location: Optional[str]
    primary_image: Optional[str]


class CoinDetail(BaseModel):
    """Full representation with all relations."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    created_at: datetime
    updated_at: datetime
    
    # All fields from model...
    category: Category
    denomination: str
    metal: Metal
    series: Optional[str]
    issuing_authority: str
    portrait_subject: Optional[str]
    status: Optional[str]
    
    # ... (all other fields)
    
    # Relations
    mint: Optional[dict]
    references: List[CoinReferenceOut]
    provenance_events: List[ProvenanceEventOut]
    images: List[CoinImageOut]
    tags: List[str]


class CoinCreate(BaseModel):
    """Schema for creating a coin."""
    category: Category
    denomination: str
    metal: Metal
    issuing_authority: str
    # ... required and optional fields
    
    # Nested creates
    references: Optional[List[dict]] = []
    provenance_events: Optional[List[dict]] = []
    tags: Optional[List[str]] = []


class CoinUpdate(BaseModel):
    """Schema for updating (all fields optional)."""
    category: Optional[Category] = None
    denomination: Optional[str] = None
    # ... all fields optional


class PaginatedCoins(BaseModel):
    items: List[CoinListItem]
    total: int
    page: int
    per_page: int
    pages: int
```

---

## 5. LLM Integration

### 5.1 Service Design

```python
# app/services/claude.py
from anthropic import Anthropic
from pydantic import BaseModel
from typing import Optional
import json

client = Anthropic()

PARSE_LISTING_PROMPT = """You are a numismatic data extraction assistant specializing in ancient Roman coins.

Extract structured data from this auction listing. Return valid JSON matching the schema below.
Use null for fields not present. Years should be integers (negative for BC).

<schema>
{
  "denomination": "string",
  "metal": "gold|silver|billon|bronze|orichalcum|copper",
  "issuing_authority": "string (ruler name)",
  "portrait_subject": "string or null",
  "reign_start": "int (negative for BC)",
  "reign_end": "int",
  "mint_year_start": "int or null",
  "mint_year_end": "int or null",
  "weight_g": "float or null",
  "diameter_mm": "float or null",
  "die_axis": "int 1-12 or null",
  "mint_name": "string or null",
  "obverse_legend": "string",
  "obverse_description": "string",
  "reverse_legend": "string",
  "reverse_description": "string",
  "exergue": "string or null",
  "references": [{"system": "ric|crawford|rpc|rsc|bmcre|sear", "volume": "string", "number": "string"}],
  "grade": "string or null",
  "grade_service": "ngc|pcgs|self|dealer or null",
  "surface_issues": ["string"],
  "auction_house": "string or null",
  "lot_number": "string or null",
  "price": "float or null",
  "currency": "string or null"
}
</schema>

<listing>
{listing_text}
</listing>

Return only valid JSON, no explanation."""


async def parse_auction_listing(listing_text: str) -> dict:
    """Extract structured coin data from auction listing text."""
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=2000,
        messages=[{
            "role": "user",
            "content": PARSE_LISTING_PROMPT.format(listing_text=listing_text)
        }]
    )
    
    return json.loads(response.content[0].text)


NATURAL_QUERY_PROMPT = """You are a search assistant for a Roman coin collection database.

Convert the user's natural language query into a structured filter object.

Available filter fields:
- category: republic, imperial, provincial, byzantine, greek
- metal: gold, silver, billon, bronze
- denomination: Denarius, Sestertius, As, Aureus, Antoninianus, Solidus, Follis, etc.
- issuing_authority: ruler name (Augustus, Nero, Trajan, etc.)
- mint_name: Rome, Lugdunum, Antioch, etc.
- reign_start_gte, reign_end_lte: year integers (negative for BC)
- acquisition_price_gte, acquisition_price_lte: price bounds
- grade: VF, XF, AU, etc.
- for_sale: boolean
- tags: array of strings

<query>{user_query}</query>

Return JSON with applicable filters only. Example:
{{"metal": "silver", "issuing_authority": "Augustus", "acquisition_price_lte": 500}}"""


async def natural_language_search(query: str) -> dict:
    """Convert natural language to filter parameters."""
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=500,
        messages=[{
            "role": "user",
            "content": NATURAL_QUERY_PROMPT.format(user_query=query)
        }]
    )
    
    return json.loads(response.content[0].text)


async def identify_coin_from_image(image_base64: str, context: Optional[str] = None) -> dict:
    """Identify a coin from an image using vision."""
    prompt = "Identify this ancient coin. Provide: likely ruler, denomination, mint (if determinable), approximate date range, and suggested catalog references (RIC, etc.)."
    
    if context:
        prompt += f"\n\nAdditional context: {context}"
    
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": [
                {"type": "image", "source": {"type": "base64", "media_type": "image/jpeg", "data": image_base64}},
                {"type": "text", "text": prompt}
            ]
        }]
    )
    
    return {"identification": response.content[0].text}


async def expand_legend(legend: str) -> str:
    """Expand abbreviated Latin legend."""
    response = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=300,
        messages=[{
            "role": "user",
            "content": f"Expand this Roman coin legend abbreviation to its full Latin form with English translation:\n\n{legend}"
        }]
    )
    
    return response.content[0].text
```

### 5.2 LLM Endpoints

```python
# app/routers/llm.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from app.services import claude

router = APIRouter(prefix="/api/llm", tags=["LLM"])


class ParseListingRequest(BaseModel):
    listing_text: str


class NaturalQueryRequest(BaseModel):
    query: str


class IdentifyRequest(BaseModel):
    image_base64: str
    context: Optional[str] = None


class ExpandLegendRequest(BaseModel):
    legend: str


@router.post("/parse-listing")
async def parse_listing(request: ParseListingRequest):
    """Extract structured data from auction listing text."""
    try:
        result = await claude.parse_auction_listing(request.listing_text)
        return {"success": True, "data": result}
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.post("/search/query")
async def natural_search(request: NaturalQueryRequest):
    """Convert natural language to search filters."""
    filters = await claude.natural_language_search(request.query)
    return {"filters": filters}


@router.post("/identify")
async def identify_coin(request: IdentifyRequest):
    """Identify coin from image."""
    result = await claude.identify_coin_from_image(
        request.image_base64, 
        request.context
    )
    return result


@router.post("/expand-legend")
async def expand_legend(request: ExpandLegendRequest):
    """Expand abbreviated legend."""
    expanded = await claude.expand_legend(request.legend)
    return {"original": request.legend, "expanded": expanded}
```

---

## 6. Frontend Architecture (React)

### 6.1 Design System

**Visual Language**
- Clean, minimal interface inspired by Linear, Notion, Raycast
- Dark mode default with light mode option
- Subtle animations and transitions (Framer Motion)
- Dense information display with good hierarchy
- Card-based layouts with hover states

**Color Palette**
```css
/* Semantic colors */
--gold: #D4AF37;      /* Gold coins, premium indicators */
--silver: #C0C0C0;    /* Silver coins */
--bronze: #CD7F32;    /* Bronze coins */
--accent: #6366F1;    /* Primary actions (Indigo) */
--success: #10B981;   /* Positive states */
--warning: #F59E0B;   /* Caution states */
--danger: #EF4444;    /* Destructive actions */
```

### 6.2 Core Components

#### CoinCard.tsx
```tsx
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { CoinListItem } from "@/types/coin";

interface CoinCardProps {
  coin: CoinListItem;
  selected?: boolean;
  onSelect?: (id: number) => void;
  onClick?: (id: number) => void;
}

export function CoinCard({ coin, selected, onSelect, onClick }: CoinCardProps) {
  const metalColors = {
    gold: "bg-yellow-500/10 text-yellow-600 border-yellow-500/20",
    silver: "bg-slate-500/10 text-slate-600 border-slate-500/20",
    bronze: "bg-orange-500/10 text-orange-600 border-orange-500/20",
    billon: "bg-zinc-500/10 text-zinc-600 border-zinc-500/20",
  };

  return (
    <Card 
      className={cn(
        "group cursor-pointer transition-all hover:shadow-lg hover:border-accent/50",
        selected && "ring-2 ring-accent"
      )}
      onClick={() => onClick?.(coin.id)}
    >
      {/* Image */}
      <div className="aspect-square bg-muted relative overflow-hidden">
        {coin.primary_image ? (
          <img 
            src={`/api/images/${coin.primary_image}`} 
            alt={`${coin.issuing_authority} ${coin.denomination}`}
            className="object-cover w-full h-full group-hover:scale-105 transition-transform"
          />
        ) : (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            No Image
          </div>
        )}
        
        {/* Selection checkbox */}
        {onSelect && (
          <div 
            className="absolute top-2 left-2 opacity-0 group-hover:opacity-100 transition-opacity"
            onClick={(e) => { e.stopPropagation(); onSelect(coin.id); }}
          >
            <Checkbox checked={selected} />
          </div>
        )}
        
        {/* Metal badge */}
        <Badge 
          variant="outline" 
          className={cn("absolute top-2 right-2", metalColors[coin.metal])}
        >
          {coin.metal}
        </Badge>
      </div>
      
      <CardContent className="p-3">
        <div className="font-medium truncate">{coin.issuing_authority}</div>
        <div className="text-sm text-muted-foreground truncate">
          {coin.denomination}
          {coin.mint_name && ` • ${coin.mint_name}`}
        </div>
        <div className="flex justify-between items-center mt-2">
          <span className="text-xs text-muted-foreground">{coin.grade || "—"}</span>
          {coin.acquisition_price && (
            <span className="text-sm font-medium">
              ${coin.acquisition_price.toLocaleString()}
            </span>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
```

#### CoinFilters.tsx
```tsx
import { useFilterStore } from "@/stores/filterStore";
import { useVocabularies } from "@/hooks/useVocabularies";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { Button } from "@/components/ui/button";
import { X } from "lucide-react";

export function CoinFilters() {
  const filters = useFilterStore();
  const { rulers, mints, denominations } = useVocabularies();
  
  const activeFilterCount = Object.values(filters).filter(Boolean).length;
  
  return (
    <div className="space-y-4 p-4 border-r min-w-[280px]">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">Filters</h3>
        {activeFilterCount > 0 && (
          <Button variant="ghost" size="sm" onClick={filters.reset}>
            <X className="w-4 h-4 mr-1" />
            Clear ({activeFilterCount})
          </Button>
        )}
      </div>
      
      {/* Category */}
      <div className="space-y-2">
        <label className="text-sm font-medium">Category</label>
        <Select value={filters.category || ""} onValueChange={filters.setCategory}>
          <SelectTrigger>
            <SelectValue placeholder="All categories" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">All</SelectItem>
            <SelectItem value="republic">Republic</SelectItem>
            <SelectItem value="imperial">Imperial</SelectItem>
            <SelectItem value="provincial">Provincial</SelectItem>
            <SelectItem value="byzantine">Byzantine</SelectItem>
          </SelectContent>
        </Select>
      </div>
      
      {/* Metal */}
      <div className="space-y-2">
        <label className="text-sm font-medium">Metal</label>
        <div className="flex flex-wrap gap-2">
          {["gold", "silver", "billon", "bronze"].map((metal) => (
            <Button
              key={metal}
              variant={filters.metal === metal ? "default" : "outline"}
              size="sm"
              onClick={() => filters.setMetal(filters.metal === metal ? null : metal)}
              className="capitalize"
            >
              {metal}
            </Button>
          ))}
        </div>
      </div>
      
      {/* Ruler */}
      <div className="space-y-2">
        <label className="text-sm font-medium">Ruler</label>
        <Combobox
          options={rulers.map(r => ({ value: r.name, label: r.name }))}
          value={filters.issuing_authority}
          onChange={filters.setIssuingAuthority}
          placeholder="Search rulers..."
        />
      </div>
      
      {/* Mint */}
      <div className="space-y-2">
        <label className="text-sm font-medium">Mint</label>
        <Combobox
          options={mints.map(m => ({ value: m.name, label: m.name }))}
          value={filters.mint_name}
          onChange={filters.setMintName}
          placeholder="Search mints..."
        />
      </div>
      
      {/* Price Range */}
      <div className="space-y-2">
        <label className="text-sm font-medium">
          Price Range: ${filters.priceRange[0]} - ${filters.priceRange[1]}
        </label>
        <Slider
          value={filters.priceRange}
          onValueChange={filters.setPriceRange}
          min={0}
          max={5000}
          step={50}
        />
      </div>
      
      {/* Date Range */}
      <div className="space-y-2">
        <label className="text-sm font-medium">Reign Period</label>
        <div className="grid grid-cols-2 gap-2">
          <Input
            type="number"
            placeholder="From (BC=-)"
            value={filters.reign_start_gte || ""}
            onChange={(e) => filters.setReignStart(e.target.value ? parseInt(e.target.value) : null)}
          />
          <Input
            type="number"
            placeholder="To"
            value={filters.reign_end_lte || ""}
            onChange={(e) => filters.setReignEnd(e.target.value ? parseInt(e.target.value) : null)}
          />
        </div>
      </div>
      
      {/* Storage Location */}
      <div className="space-y-2">
        <label className="text-sm font-medium">Storage</label>
        <Select value={filters.storage_location || ""} onValueChange={filters.setStorageLocation}>
          <SelectTrigger>
            <SelectValue placeholder="All locations" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="">All</SelectItem>
            <SelectItem value="SlabBox1">Slab Box 1</SelectItem>
            <SelectItem value="Velv1">Velvet Tray 1</SelectItem>
            <SelectItem value="Velv2">Velvet Tray 2</SelectItem>
            <SelectItem value="Velv3">Velvet Tray 3</SelectItem>
          </SelectContent>
        </Select>
      </div>
    </div>
  );
}
```

#### NaturalSearchBar.tsx
```tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useLLMSearch } from "@/hooks/useLLM";
import { useFilterStore } from "@/stores/filterStore";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Sparkles, Loader2 } from "lucide-react";

export function NaturalSearchBar() {
  const [query, setQuery] = useState("");
  const { mutate: search, isPending } = useLLMSearch();
  const filters = useFilterStore();
  
  const handleSearch = () => {
    if (!query.trim()) return;
    
    search(query, {
      onSuccess: (result) => {
        // Apply returned filters
        Object.entries(result.filters).forEach(([key, value]) => {
          filters.setFilter(key, value);
        });
        setQuery("");
      }
    });
  };
  
  return (
    <div className="relative flex-1 max-w-xl">
      <Sparkles className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
      <Input
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        onKeyDown={(e) => e.key === "Enter" && handleSearch()}
        placeholder="Try: 'Severan silver under $200' or 'gold coins from eastern mints'"
        className="pl-10 pr-20"
      />
      <Button 
        size="sm" 
        onClick={handleSearch}
        disabled={isPending || !query.trim()}
        className="absolute right-1 top-1/2 -translate-y-1/2"
      >
        {isPending ? <Loader2 className="w-4 h-4 animate-spin" /> : "Search"}
      </Button>
    </div>
  );
}
```

#### ParseListingDialog.tsx
```tsx
import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useParseListing } from "@/hooks/useLLM";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Loader2, Sparkles, Check, AlertCircle } from "lucide-react";

interface ParseListingDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function ParseListingDialog({ open, onOpenChange }: ParseListingDialogProps) {
  const [listingText, setListingText] = useState("");
  const [parsedData, setParsedData] = useState<any>(null);
  const navigate = useNavigate();
  
  const { mutate: parse, isPending, error } = useParseListing();
  
  const handleParse = () => {
    parse(listingText, {
      onSuccess: (data) => {
        setParsedData(data);
      }
    });
  };
  
  const handleUseData = () => {
    // Navigate to add coin page with pre-filled data
    navigate("/coins/new", { state: { prefill: parsedData } });
    onOpenChange(false);
    setParsedData(null);
    setListingText("");
  };
  
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-purple-500" />
            Parse Auction Listing
          </DialogTitle>
          <DialogDescription>
            Paste an auction listing and let AI extract structured data
          </DialogDescription>
        </DialogHeader>
        
        <div className="flex-1 overflow-auto space-y-4">
          {!parsedData ? (
            <Textarea
              value={listingText}
              onChange={(e) => setListingText(e.target.value)}
              placeholder="Paste auction listing text here...

Example:
Augustus (27 BC-AD 14). AR Denarius (19mm, 3.89 gm, 7h). Lugdunum, 2 BC-AD 4. 
CAESAR AVGVSTVS DIVI F PATER PATRIAE, laureate head right / AVGVSTI F COS DESIG 
PRINC IVVENT, Gaius and Lucius Caesars standing facing. RIC I 207. NGC Choice XF."
              rows={12}
              className="font-mono text-sm"
            />
          ) : (
            <div className="space-y-3">
              <div className="flex items-center gap-2 text-green-600">
                <Check className="w-5 h-5" />
                <span className="font-medium">Successfully extracted!</span>
              </div>
              
              <div className="grid grid-cols-2 gap-3 text-sm">
                {Object.entries(parsedData).map(([key, value]) => (
                  value && (
                    <div key={key} className="flex flex-col">
                      <span className="text-muted-foreground capitalize">
                        {key.replace(/_/g, " ")}
                      </span>
                      <span className="font-medium">
                        {typeof value === "object" ? JSON.stringify(value) : String(value)}
                      </span>
                    </div>
                  )
                ))}
              </div>
            </div>
          )}
          
          {error && (
            <div className="flex items-center gap-2 text-red-600 text-sm">
              <AlertCircle className="w-4 h-4" />
              Failed to parse listing. Try again with clearer text.
            </div>
          )}
        </div>
        
        <DialogFooter>
          {!parsedData ? (
            <>
              <Button variant="outline" onClick={() => onOpenChange(false)}>
                Cancel
              </Button>
              <Button 
                onClick={handleParse} 
                disabled={isPending || !listingText.trim()}
              >
                {isPending ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Extracting...
                  </>
                ) : (
                  <>
                    <Sparkles className="w-4 h-4 mr-2" />
                    Extract Data
                  </>
                )}
              </Button>
            </>
          ) : (
            <>
              <Button 
                variant="outline" 
                onClick={() => { setParsedData(null); setListingText(""); }}
              >
                Try Another
              </Button>
              <Button onClick={handleUseData}>
                Use This Data
              </Button>
            </>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

#### CoinDetail.tsx (Tabbed View)
```tsx
import { useParams, useNavigate } from "react-router-dom";
import { useCoin, useDeleteCoin } from "@/hooks/useCoins";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { 
  ArrowLeft, Edit, Trash2, ExternalLink, 
  Scale, Ruler, CircleDot, Calendar 
} from "lucide-react";
import { CoinImageGallery } from "./CoinImageGallery";
import { ReferenceList } from "../references/ReferenceList";
import { ProvenanceTimeline } from "../provenance/ProvenanceTimeline";
import { LegendExpander } from "../llm/LegendExpander";

export function CoinDetail() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { data: coin, isLoading } = useCoin(Number(id));
  const deleteMutation = useDeleteCoin();
  
  if (isLoading) return <CoinDetailSkeleton />;
  if (!coin) return <div>Coin not found</div>;
  
  const handleDelete = () => {
    if (confirm("Delete this coin? This cannot be undone.")) {
      deleteMutation.mutate(coin.id, {
        onSuccess: () => navigate("/")
      });
    }
  };
  
  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="icon" onClick={() => navigate(-1)}>
            <ArrowLeft className="w-5 h-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-bold">{coin.issuing_authority}</h1>
            <p className="text-muted-foreground">
              {coin.denomination} • {coin.mint?.name || "Unknown mint"}
            </p>
          </div>
        </div>
        
        <div className="flex items-center gap-2">
          <Button variant="outline" onClick={() => navigate(`/coins/${id}/edit`)}>
            <Edit className="w-4 h-4 mr-2" />
            Edit
          </Button>
          <Button variant="destructive" onClick={handleDelete}>
            <Trash2 className="w-4 h-4 mr-2" />
            Delete
          </Button>
        </div>
      </div>
      
      {/* Main Content */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left: Images */}
        <div>
          <CoinImageGallery 
            images={coin.images} 
            coinId={coin.id}
            onUpload={() => {}}
          />
        </div>
        
        {/* Right: Details */}
        <div>
          {/* Quick Stats */}
          <div className="grid grid-cols-4 gap-4 mb-6">
            <div className="text-center p-3 bg-muted rounded-lg">
              <Scale className="w-5 h-5 mx-auto mb-1 text-muted-foreground" />
              <div className="font-semibold">{coin.weight_g || "—"}g</div>
              <div className="text-xs text-muted-foreground">Weight</div>
            </div>
            <div className="text-center p-3 bg-muted rounded-lg">
              <Ruler className="w-5 h-5 mx-auto mb-1 text-muted-foreground" />
              <div className="font-semibold">{coin.diameter_mm || "—"}mm</div>
              <div className="text-xs text-muted-foreground">Diameter</div>
            </div>
            <div className="text-center p-3 bg-muted rounded-lg">
              <CircleDot className="w-5 h-5 mx-auto mb-1 text-muted-foreground" />
              <div className="font-semibold">{coin.die_axis || "—"}h</div>
              <div className="text-xs text-muted-foreground">Die Axis</div>
            </div>
            <div className="text-center p-3 bg-muted rounded-lg">
              <Calendar className="w-5 h-5 mx-auto mb-1 text-muted-foreground" />
              <div className="font-semibold">
                {coin.mint_year_start && coin.mint_year_end 
                  ? `${coin.mint_year_start}-${coin.mint_year_end}`
                  : coin.mint_year_start || "—"
                }
              </div>
              <div className="text-xs text-muted-foreground">Minted</div>
            </div>
          </div>
          
          {/* Badges */}
          <div className="flex flex-wrap gap-2 mb-6">
            <Badge variant="outline">{coin.category}</Badge>
            <Badge variant="outline">{coin.metal}</Badge>
            {coin.grade && <Badge>{coin.grade}</Badge>}
            {coin.rarity && <Badge variant="secondary">{coin.rarity}</Badge>}
          </div>
          
          {/* Tabs */}
          <Tabs defaultValue="design" className="w-full">
            <TabsList className="grid w-full grid-cols-4">
              <TabsTrigger value="design">Design</TabsTrigger>
              <TabsTrigger value="references">References</TabsTrigger>
              <TabsTrigger value="provenance">Provenance</TabsTrigger>
              <TabsTrigger value="notes">Notes</TabsTrigger>
            </TabsList>
            
            <TabsContent value="design" className="space-y-4 mt-4">
              {/* Obverse */}
              <div>
                <h3 className="font-semibold mb-2">Obverse</h3>
                {coin.obverse_legend && (
                  <div className="mb-2">
                    <LegendExpander legend={coin.obverse_legend} />
                  </div>
                )}
                <p className="text-sm text-muted-foreground">
                  {coin.obverse_description || "No description"}
                </p>
              </div>
              
              {/* Reverse */}
              <div>
                <h3 className="font-semibold mb-2">Reverse</h3>
                {coin.reverse_legend && (
                  <div className="mb-2">
                    <LegendExpander legend={coin.reverse_legend} />
                  </div>
                )}
                <p className="text-sm text-muted-foreground">
                  {coin.reverse_description || "No description"}
                </p>
                {coin.exergue && (
                  <p className="text-sm mt-1">
                    <span className="text-muted-foreground">Exergue:</span> {coin.exergue}
                  </p>
                )}
              </div>
            </TabsContent>
            
            <TabsContent value="references" className="mt-4">
              <ReferenceList references={coin.references} coinId={coin.id} />
            </TabsContent>
            
            <TabsContent value="provenance" className="mt-4">
              <ProvenanceTimeline events={coin.provenance_events} coinId={coin.id} />
              
              {coin.acquisition_url && (
                <Button variant="link" className="mt-4 p-0" asChild>
                  <a href={coin.acquisition_url} target="_blank" rel="noopener">
                    View Original Listing
                    <ExternalLink className="w-4 h-4 ml-1" />
                  </a>
                </Button>
              )}
            </TabsContent>
            
            <TabsContent value="notes" className="mt-4 space-y-4">
              {coin.historical_significance && (
                <div>
                  <h3 className="font-semibold mb-1">Historical Significance</h3>
                  <p className="text-sm text-muted-foreground">{coin.historical_significance}</p>
                </div>
              )}
              {coin.style_notes && (
                <div>
                  <h3 className="font-semibold mb-1">Style Notes</h3>
                  <p className="text-sm text-muted-foreground">{coin.style_notes}</p>
                </div>
              )}
              {coin.personal_notes && (
                <div>
                  <h3 className="font-semibold mb-1">Personal Notes</h3>
                  <p className="text-sm text-muted-foreground">{coin.personal_notes}</p>
                </div>
              )}
            </TabsContent>
          </Tabs>
        </div>
      </div>
    </div>
  );
}
```

### 6.3 Data Fetching Hooks

```typescript
// hooks/useCoins.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { CoinListItem, CoinDetail, CoinCreate, CoinUpdate } from "@/types/coin";
import { useFilterStore } from "@/stores/filterStore";

export function useCoins() {
  const filters = useFilterStore();
  
  return useQuery({
    queryKey: ["coins", filters.toParams()],
    queryFn: () => api.get<PaginatedResponse<CoinListItem>>("/api/coins", { 
      params: filters.toParams() 
    }),
  });
}

export function useCoin(id: number) {
  return useQuery({
    queryKey: ["coin", id],
    queryFn: () => api.get<CoinDetail>(`/api/coins/${id}`),
    enabled: !!id,
  });
}

export function useCreateCoin() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (data: CoinCreate) => api.post<CoinDetail>("/api/coins", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["coins"] });
    },
  });
}

export function useUpdateCoin() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: CoinUpdate }) =>
      api.put<CoinDetail>(`/api/coins/${id}`, data),
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: ["coins"] });
      queryClient.invalidateQueries({ queryKey: ["coin", id] });
    },
  });
}

export function useDeleteCoin() {
  const queryClient = useQueryClient();
  
  return useMutation({
    mutationFn: (id: number) => api.delete(`/api/coins/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["coins"] });
    },
  });
}

// hooks/useLLM.ts
export function useParseListing() {
  return useMutation({
    mutationFn: (text: string) => 
      api.post<{ data: Partial<CoinCreate> }>("/api/llm/parse-listing", { 
        listing_text: text 
      }),
  });
}

export function useLLMSearch() {
  return useMutation({
    mutationFn: (query: string) =>
      api.post<{ filters: Record<string, any> }>("/api/llm/search/query", { query }),
  });
}

export function useExpandLegend() {
  return useMutation({
    mutationFn: (legend: string) =>
      api.post<{ expanded: string }>("/api/llm/expand-legend", { legend }),
  });
}
```

### 6.4 State Management

```typescript
// stores/filterStore.ts
import { create } from "zustand";
import { persist } from "zustand/middleware";

interface FilterState {
  category: string | null;
  metal: string | null;
  issuing_authority: string | null;
  mint_name: string | null;
  denomination: string | null;
  priceRange: [number, number];
  reign_start_gte: number | null;
  reign_end_lte: number | null;
  grade_service: string | null;
  storage_location: string | null;
  for_sale: boolean | null;
  
  // Actions
  setCategory: (v: string | null) => void;
  setMetal: (v: string | null) => void;
  setIssuingAuthority: (v: string | null) => void;
  setMintName: (v: string | null) => void;
  setPriceRange: (v: [number, number]) => void;
  setReignStart: (v: number | null) => void;
  setReignEnd: (v: number | null) => void;
  setStorageLocation: (v: string | null) => void;
  setFilter: (key: string, value: any) => void;
  reset: () => void;
  toParams: () => Record<string, any>;
}

const initialState = {
  category: null,
  metal: null,
  issuing_authority: null,
  mint_name: null,
  denomination: null,
  priceRange: [0, 5000] as [number, number],
  reign_start_gte: null,
  reign_end_lte: null,
  grade_service: null,
  storage_location: null,
  for_sale: null,
};

export const useFilterStore = create<FilterState>()(
  persist(
    (set, get) => ({
      ...initialState,
      
      setCategory: (category) => set({ category }),
      setMetal: (metal) => set({ metal }),
      setIssuingAuthority: (issuing_authority) => set({ issuing_authority }),
      setMintName: (mint_name) => set({ mint_name }),
      setPriceRange: (priceRange) => set({ priceRange }),
      setReignStart: (reign_start_gte) => set({ reign_start_gte }),
      setReignEnd: (reign_end_lte) => set({ reign_end_lte }),
      setStorageLocation: (storage_location) => set({ storage_location }),
      
      setFilter: (key, value) => set({ [key]: value }),
      
      reset: () => set(initialState),
      
      toParams: () => {
        const state = get();
        const params: Record<string, any> = {};
        
        Object.entries(state).forEach(([key, value]) => {
          if (typeof value === "function") return;
          if (value === null || value === undefined) return;
          if (key === "priceRange") {
            if (value[0] > 0) params.acquisition_price_gte = value[0];
            if (value[1] < 5000) params.acquisition_price_lte = value[1];
            return;
          }
          params[key] = value;
        });
        
        return params;
      },
    }),
    { name: "coinstack-filters" }
  )
);

// stores/uiStore.ts
import { create } from "zustand";

interface UIState {
  sidebarOpen: boolean;
  viewMode: "grid" | "table";
  parseListingOpen: boolean;
  commandPaletteOpen: boolean;
  
  toggleSidebar: () => void;
  setViewMode: (mode: "grid" | "table") => void;
  setParseListingOpen: (open: boolean) => void;
  setCommandPaletteOpen: (open: boolean) => void;
}

export const useUIStore = create<UIState>((set) => ({
  sidebarOpen: true,
  viewMode: "grid",
  parseListingOpen: false,
  commandPaletteOpen: false,
  
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
  setViewMode: (viewMode) => set({ viewMode }),
  setParseListingOpen: (parseListingOpen) => set({ parseListingOpen }),
  setCommandPaletteOpen: (commandPaletteOpen) => set({ commandPaletteOpen }),
}));
```

### 6.5 App Shell & Routing

```tsx
// App.tsx
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "@/components/ui/sonner";
import { AppShell } from "@/components/layout/AppShell";

import { CollectionPage } from "@/pages/CollectionPage";
import { CoinDetailPage } from "@/pages/CoinDetailPage";
import { AddCoinPage } from "@/pages/AddCoinPage";
import { EditCoinPage } from "@/pages/EditCoinPage";
import { ImportPage } from "@/pages/ImportPage";
import { StatsPage } from "@/pages/StatsPage";
import { SettingsPage } from "@/pages/SettingsPage";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 1,
    },
  },
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider defaultTheme="dark" storageKey="coinstack-theme">
        <BrowserRouter>
          <AppShell>
            <Routes>
              <Route path="/" element={<CollectionPage />} />
              <Route path="/coins/new" element={<AddCoinPage />} />
              <Route path="/coins/:id" element={<CoinDetailPage />} />
              <Route path="/coins/:id/edit" element={<EditCoinPage />} />
              <Route path="/import" element={<ImportPage />} />
              <Route path="/stats" element={<StatsPage />} />
              <Route path="/settings" element={<SettingsPage />} />
            </Routes>
          </AppShell>
        </BrowserRouter>
        <Toaster />
      </ThemeProvider>
    </QueryClientProvider>
  );
}

// components/layout/AppShell.tsx
import { ReactNode } from "react";
import { Header } from "./Header";
import { Sidebar } from "./Sidebar";
import { CommandPalette } from "./CommandPalette";
import { useUIStore } from "@/stores/uiStore";
import { cn } from "@/lib/utils";

export function AppShell({ children }: { children: ReactNode }) {
  const { sidebarOpen } = useUIStore();
  
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <div className="flex">
        <Sidebar />
        <main className={cn(
          "flex-1 transition-all duration-200",
          sidebarOpen ? "ml-64" : "ml-16"
        )}>
          {children}
        </main>
      </div>
      <CommandPalette />
    </div>
  );
}

// components/layout/Sidebar.tsx
import { NavLink } from "react-router-dom";
import { useUIStore } from "@/stores/uiStore";
import { cn } from "@/lib/utils";
import { 
  Coins, BarChart3, Upload, Settings, 
  ChevronLeft, ChevronRight 
} from "lucide-react";
import { Button } from "@/components/ui/button";

const navItems = [
  { to: "/", icon: Coins, label: "Collection" },
  { to: "/stats", icon: BarChart3, label: "Statistics" },
  { to: "/import", icon: Upload, label: "Import" },
  { to: "/settings", icon: Settings, label: "Settings" },
];

export function Sidebar() {
  const { sidebarOpen, toggleSidebar } = useUIStore();
  
  return (
    <aside className={cn(
      "fixed left-0 top-14 bottom-0 z-40 border-r bg-card transition-all duration-200",
      sidebarOpen ? "w-64" : "w-16"
    )}>
      <nav className="flex flex-col gap-1 p-2">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) => cn(
              "flex items-center gap-3 px-3 py-2 rounded-md transition-colors",
              isActive 
                ? "bg-accent text-accent-foreground" 
                : "hover:bg-muted"
            )}
          >
            <Icon className="w-5 h-5 flex-shrink-0" />
            {sidebarOpen && <span>{label}</span>}
          </NavLink>
        ))}
      </nav>
      
      <Button
        variant="ghost"
        size="icon"
        className="absolute bottom-4 right-2"
        onClick={toggleSidebar}
      >
        {sidebarOpen ? <ChevronLeft /> : <ChevronRight />}
      </Button>
    </aside>
  );
}
```

### 6.6 Key UI Features

| Feature | Implementation |
|---------|----------------|
| **Command Palette** | `Cmd+K` for quick actions (add coin, search, navigate) |
| **Keyboard Navigation** | Arrow keys in grid, Enter to open detail |
| **Bulk Selection** | Shift+click range, Cmd+click individual |
| **Drag & Drop** | Reorder images, upload by dropping |
| **Optimistic Updates** | Instant UI feedback on mutations |
| **Infinite Scroll** | Load more coins on scroll (optional) |
| **Toast Notifications** | Sonner for success/error feedback |
| **Dark/Light Mode** | System preference with manual toggle |
| **Responsive** | Mobile-first, collapsible sidebar |

---

## 7. Test-Driven Development Plan

### 7.1 Test Structure

```
tests/
├── conftest.py                 # Shared fixtures
├── unit/
│   ├── test_schemas.py         # Pydantic validation
│   ├── test_crud.py            # Database operations
│   └── test_services.py        # Business logic
├── api/
│   ├── test_coins_api.py       # Coin endpoints
│   ├── test_search_api.py      # Search endpoints
│   ├── test_llm_api.py         # LLM endpoints (mocked)
│   └── test_import_api.py      # Import/export
├── integration/
│   ├── test_full_pipeline.py   # CSV → DB → API → UI
│   └── test_llm_integration.py # Real API calls (optional)
└── e2e/
    └── test_playwright.py      # Browser tests (optional)
```

### 7.2 Test Phases

#### Phase 1: Schemas & Validation (2h)

```python
# tests/unit/test_schemas.py

def test_coin_create_valid():
    """Valid coin data passes validation."""
    data = {
        "category": "imperial",
        "denomination": "Denarius",
        "metal": "silver",
        "issuing_authority": "Augustus"
    }
    coin = CoinCreate(**data)
    assert coin.issuing_authority == "Augustus"


def test_coin_create_invalid_category():
    """Invalid category raises ValidationError."""
    with pytest.raises(ValidationError):
        CoinCreate(category="invalid", denomination="Denarius", metal="silver", issuing_authority="Augustus")


def test_coin_create_invalid_metal():
    """Invalid metal raises ValidationError."""
    with pytest.raises(ValidationError):
        CoinCreate(category="imperial", denomination="Denarius", metal="platinum", issuing_authority="Augustus")


def test_date_parsing_ad():
    """AD dates parse correctly."""
    # Implementation depends on how you handle dates in schema


def test_date_parsing_bc():
    """BC dates become negative integers."""
    pass


def test_weight_decimal_precision():
    """Weight maintains 2 decimal places."""
    coin = CoinCreate(
        category="imperial", 
        denomination="Denarius", 
        metal="silver",
        issuing_authority="Augustus",
        weight_g=3.456
    )
    # Check rounding behavior


def test_reference_system_enum():
    """Reference system must be valid enum."""
    ref = CoinReferenceCreate(system="ric", number="207")
    assert ref.system == ReferenceSystem.RIC


def test_provenance_event_types():
    """Provenance type must be valid enum."""
    event = ProvenanceEventCreate(event_type="auction")
    assert event.event_type == ProvenanceType.AUCTION
```

#### Phase 2: CRUD Operations (3h)

```python
# tests/unit/test_crud.py

@pytest.fixture
def db_session():
    """Create test database session."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def sample_mint(db_session):
    """Create sample mint."""
    mint = Mint(name="Rome", province="Italia")
    db_session.add(mint)
    db_session.commit()
    return mint


def test_create_coin(db_session, sample_mint):
    """Create coin and retrieve by ID."""
    coin_data = CoinCreate(
        category="imperial",
        denomination="Denarius",
        metal="silver",
        issuing_authority="Augustus"
    )
    coin = crud.create_coin(db_session, coin_data)
    
    assert coin.id is not None
    assert coin.issuing_authority == "Augustus"


def test_list_coins_filter_ruler(db_session):
    """Filter coins by ruler."""
    # Create 3 Augustus coins, 2 Nero coins
    for _ in range(3):
        crud.create_coin(db_session, CoinCreate(
            category="imperial", denomination="Denarius", 
            metal="silver", issuing_authority="Augustus"
        ))
    for _ in range(2):
        crud.create_coin(db_session, CoinCreate(
            category="imperial", denomination="Denarius",
            metal="silver", issuing_authority="Nero"
        ))
    
    results = crud.list_coins(db_session, issuing_authority="Augustus")
    assert len(results) == 3


def test_list_coins_filter_multiple(db_session):
    """Filter by multiple criteria."""
    crud.create_coin(db_session, CoinCreate(
        category="imperial", denomination="Aureus",
        metal="gold", issuing_authority="Augustus"
    ))
    crud.create_coin(db_session, CoinCreate(
        category="imperial", denomination="Denarius",
        metal="silver", issuing_authority="Augustus"
    ))
    
    results = crud.list_coins(db_session, issuing_authority="Augustus", metal="gold")
    assert len(results) == 1
    assert results[0].denomination == "Aureus"


def test_update_coin(db_session):
    """Update coin fields."""
    coin = crud.create_coin(db_session, CoinCreate(
        category="imperial", denomination="Denarius",
        metal="silver", issuing_authority="Augustus"
    ))
    
    updated = crud.update_coin(db_session, coin.id, CoinUpdate(
        storage_location="SlabBox1"
    ))
    
    assert updated.storage_location == "SlabBox1"


def test_delete_coin(db_session):
    """Delete coin and verify cascade."""
    coin = crud.create_coin(db_session, CoinCreate(
        category="imperial", denomination="Denarius",
        metal="silver", issuing_authority="Augustus"
    ))
    coin_id = coin.id
    
    crud.delete_coin(db_session, coin_id)
    
    assert crud.get_coin(db_session, coin_id) is None


def test_add_reference(db_session):
    """Add reference to coin."""
    coin = crud.create_coin(db_session, CoinCreate(
        category="imperial", denomination="Denarius",
        metal="silver", issuing_authority="Augustus"
    ))
    
    ref = crud.add_reference(db_session, coin.id, CoinReferenceCreate(
        system="ric", volume="I", number="207", is_primary=True
    ))
    
    assert ref.coin_id == coin.id
    assert ref.is_primary is True


def test_add_provenance_event(db_session):
    """Add provenance event to coin."""
    coin = crud.create_coin(db_session, CoinCreate(
        category="imperial", denomination="Denarius",
        metal="silver", issuing_authority="Augustus"
    ))
    
    event = crud.add_provenance_event(db_session, coin.id, ProvenanceEventCreate(
        event_type="auction",
        auction_house="Heritage",
        price=384.00,
        currency="USD"
    ))
    
    assert event.auction_house == "Heritage"


def test_stats_by_ruler(db_session):
    """Calculate stats grouped by ruler."""
    crud.create_coin(db_session, CoinCreate(
        category="imperial", denomination="Denarius",
        metal="silver", issuing_authority="Augustus",
        acquisition_price=100
    ))
    crud.create_coin(db_session, CoinCreate(
        category="imperial", denomination="Aureus",
        metal="gold", issuing_authority="Augustus",
        acquisition_price=2000
    ))
    
    stats = crud.get_stats_by_ruler(db_session)
    augustus_stats = next(s for s in stats if s["ruler"] == "Augustus")
    
    assert augustus_stats["count"] == 2
    assert augustus_stats["total_value"] == 2100
    assert augustus_stats["avg_value"] == 1050
```

#### Phase 3: CSV Import (2h)

```python
# tests/unit/test_import.py

@pytest.fixture
def sample_csv(tmp_path):
    """Create sample CSV matching your format."""
    csv_content = """,Temp loc,,Category,Coin type,Ruler Issuer,...
7,SlabBox1,,Roman Imperial,Denarius,Augustus,..."""
    csv_file = tmp_path / "test.csv"
    csv_file.write_text(csv_content)
    return csv_file


def test_csv_parse_headers(sample_csv):
    """Parse CSV and extract headers."""
    headers = import_service.get_csv_headers(sample_csv)
    assert "Category" in headers
    assert "Ruler Issuer" in headers


def test_csv_import_creates_coins(db_session, sample_csv):
    """Import CSV creates coin records."""
    result = import_service.import_csv(db_session, sample_csv)
    
    assert result["imported"] > 0
    assert result["errors"] == []


def test_csv_import_full_file(db_session):
    """Import your actual CSV file."""
    result = import_service.import_csv(db_session, "data/imports/collection-v1.csv")
    
    assert result["imported"] == 110  # Your row count
    
    # Verify specific coin
    augustus = crud.list_coins(db_session, issuing_authority="Augustus")
    assert len(augustus) > 0


def test_csv_import_handles_encoding(db_session, tmp_path):
    """Handle encoding issues (\\xc2, \\xa0)."""
    # Create CSV with encoding artifacts
    pass


def test_csv_import_idempotent(db_session, sample_csv):
    """Re-import doesn't create duplicates."""
    import_service.import_csv(db_session, sample_csv)
    import_service.import_csv(db_session, sample_csv)
    
    coins = crud.list_coins(db_session)
    # Check for duplicates


def test_csv_import_parses_dates(db_session):
    """Parse various date formats."""
    # "AD 14-37" → reign_start=14, reign_end=37
    # "27 BC-AD 14" → reign_start=-27, reign_end=14
    pass


def test_csv_import_parses_references(db_session):
    """Extract references from Reference column."""
    # "RIC I 207" → system=ric, volume=I, number=207
    # "Crawford 335/1c" → system=crawford, number=335/1c
    pass
```

#### Phase 4: API Endpoints (4h)

```python
# tests/api/test_coins_api.py

@pytest.fixture
def client(db_session):
    """Create test client."""
    app.dependency_overrides[get_db] = lambda: db_session
    return TestClient(app)


@pytest.fixture
def sample_coins(db_session):
    """Create sample coins for testing."""
    coins = []
    for ruler in ["Augustus", "Nero", "Trajan"]:
        coin = crud.create_coin(db_session, CoinCreate(
            category="imperial", denomination="Denarius",
            metal="silver", issuing_authority=ruler,
            acquisition_price=100
        ))
        coins.append(coin)
    return coins


def test_get_coins_list(client, sample_coins):
    """GET /api/coins returns paginated list."""
    response = client.get("/api/coins")
    
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) == 3


def test_get_coins_filter_ruler(client, sample_coins):
    """GET /api/coins?issuing_authority=Augustus filters correctly."""
    response = client.get("/api/coins?issuing_authority=Augustus")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data["items"]) == 1
    assert data["items"][0]["issuing_authority"] == "Augustus"


def test_get_coins_filter_price_range(client, sample_coins):
    """Filter by price range."""
    response = client.get("/api/coins?acquisition_price_gte=50&acquisition_price_lte=150")
    
    assert response.status_code == 200


def test_get_coins_pagination(client, db_session):
    """Pagination works correctly."""
    # Create 25 coins
    for i in range(25):
        crud.create_coin(db_session, CoinCreate(
            category="imperial", denomination="Denarius",
            metal="silver", issuing_authority=f"Ruler{i}"
        ))
    
    response = client.get("/api/coins?page=1&per_page=10")
    data = response.json()
    
    assert len(data["items"]) == 10
    assert data["total"] == 25
    assert data["pages"] == 3


def test_get_coin_detail(client, sample_coins):
    """GET /api/coins/{id} returns full detail."""
    coin_id = sample_coins[0].id
    response = client.get(f"/api/coins/{coin_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == coin_id
    assert "references" in data
    assert "provenance_events" in data


def test_get_coin_not_found(client):
    """GET /api/coins/{id} returns 404 for missing."""
    response = client.get("/api/coins/99999")
    assert response.status_code == 404


def test_create_coin(client):
    """POST /api/coins creates coin."""
    payload = {
        "category": "imperial",
        "denomination": "Aureus",
        "metal": "gold",
        "issuing_authority": "Nero",
        "acquisition_price": 5000
    }
    response = client.post("/api/coins", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert data["id"] is not None
    assert data["issuing_authority"] == "Nero"


def test_create_coin_with_references(client):
    """POST /api/coins creates coin with nested references."""
    payload = {
        "category": "republic",
        "denomination": "Denarius",
        "metal": "silver",
        "issuing_authority": "C. Malleolus",
        "references": [
            {"system": "crawford", "number": "335/1c", "is_primary": True},
            {"system": "sydenham", "number": "611"}
        ]
    }
    response = client.post("/api/coins", json=payload)
    
    assert response.status_code == 201
    data = response.json()
    assert len(data["references"]) == 2


def test_create_coin_validation_error(client):
    """POST /api/coins returns 422 for invalid data."""
    payload = {
        "category": "invalid",
        "denomination": "Denarius",
        "metal": "silver",
        "issuing_authority": "Augustus"
    }
    response = client.post("/api/coins", json=payload)
    
    assert response.status_code == 422


def test_update_coin(client, sample_coins):
    """PUT /api/coins/{id} updates coin."""
    coin_id = sample_coins[0].id
    payload = {
        "storage_location": "NewLocation",
        "personal_notes": "Updated notes"
    }
    response = client.put(f"/api/coins/{coin_id}", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["storage_location"] == "NewLocation"


def test_delete_coin(client, sample_coins):
    """DELETE /api/coins/{id} removes coin."""
    coin_id = sample_coins[0].id
    response = client.delete(f"/api/coins/{coin_id}")
    
    assert response.status_code == 204
    
    # Verify deleted
    response = client.get(f"/api/coins/{coin_id}")
    assert response.status_code == 404


def test_stats_overview(client, sample_coins):
    """GET /api/stats/overview returns summary."""
    response = client.get("/api/stats/overview")
    
    assert response.status_code == 200
    data = response.json()
    assert "total_coins" in data
    assert "total_value" in data
    assert "by_metal" in data
```

#### Phase 5: LLM Integration (3h)

```python
# tests/api/test_llm_api.py
from unittest.mock import patch, AsyncMock


@pytest.fixture
def mock_claude():
    """Mock Claude API responses."""
    with patch("app.services.claude.client") as mock:
        yield mock


def test_parse_listing_success(client, mock_claude):
    """POST /api/llm/parse-listing extracts data."""
    mock_claude.messages.create.return_value.content = [
        type("Content", (), {"text": json.dumps({
            "denomination": "Denarius",
            "metal": "silver",
            "issuing_authority": "Augustus",
            "weight_g": 3.9,
            "references": [{"system": "ric", "volume": "I", "number": "207"}]
        })})()
    ]
    
    response = client.post("/api/llm/parse-listing", json={
        "listing_text": "Augustus AR Denarius, RIC I 207, 3.9g"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["issuing_authority"] == "Augustus"


def test_parse_listing_error(client, mock_claude):
    """Handle LLM parsing errors gracefully."""
    mock_claude.messages.create.return_value.content = [
        type("Content", (), {"text": "invalid json"})()
    ]
    
    response = client.post("/api/llm/parse-listing", json={
        "listing_text": "Some garbage text"
    })
    
    assert response.status_code == 422


def test_natural_language_search(client, mock_claude):
    """POST /api/search/query converts NL to filters."""
    mock_claude.messages.create.return_value.content = [
        type("Content", (), {"text": json.dumps({
            "metal": "silver",
            "issuing_authority": "Augustus",
            "acquisition_price_lte": 500
        })})()
    ]
    
    response = client.post("/api/llm/search/query", json={
        "query": "show me Augustus silver coins under $500"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["filters"]["metal"] == "silver"


def test_expand_legend(client, mock_claude):
    """POST /api/llm/expand-legend expands abbreviation."""
    mock_claude.messages.create.return_value.content = [
        type("Content", (), {"text": "CAESAR AVGVSTVS DIVI FILIVS PATER PATRIAE\n(Caesar Augustus, Son of the Divine, Father of the Fatherland)"})()
    ]
    
    response = client.post("/api/llm/expand-legend", json={
        "legend": "CAESAR AVGVSTVS-DIVI F PATER PATRIAE"
    })
    
    assert response.status_code == 200
    assert "FILIVS" in response.json()["expanded"]
```

#### Phase 6: Integration Tests (2h)

```python
# tests/integration/test_full_pipeline.py

def test_import_then_search(client, db_session):
    """Import CSV and verify searchable."""
    # Import
    with open("data/imports/collection-v1.csv", "rb") as f:
        response = client.post("/api/import/csv", files={"file": f})
    
    assert response.status_code == 200
    assert response.json()["imported"] == 110
    
    # Search
    response = client.get("/api/coins?issuing_authority=Augustus&denomination=Denarius")
    data = response.json()
    
    assert len(data["items"]) > 0
    
    # Verify specific coin from your data
    augustus_denarius = next(
        (c for c in data["items"] if c["acquisition_price"] == 384), 
        None
    )
    assert augustus_denarius is not None


def test_full_crud_cycle(client):
    """Create, read, update, delete cycle."""
    # Create
    response = client.post("/api/coins", json={
        "category": "imperial",
        "denomination": "Sestertius",
        "metal": "bronze",
        "issuing_authority": "Hadrian"
    })
    coin_id = response.json()["id"]
    
    # Read
    response = client.get(f"/api/coins/{coin_id}")
    assert response.json()["issuing_authority"] == "Hadrian"
    
    # Update
    response = client.put(f"/api/coins/{coin_id}", json={
        "acquisition_price": 750
    })
    assert response.json()["acquisition_price"] == 750
    
    # Add reference
    response = client.post(f"/api/coins/{coin_id}/references", json={
        "system": "ric",
        "volume": "II",
        "number": "500",
        "is_primary": True
    })
    assert response.status_code == 201
    
    # Delete
    response = client.delete(f"/api/coins/{coin_id}")
    assert response.status_code == 204
```

### 7.3 Coverage Target

```bash
# Run tests with coverage
pytest --cov=app --cov-report=html --cov-fail-under=95

# Expected output
# TOTAL    95%+
```

---

## 8. Development Roadmap

### Phase 1: Foundation (Week 1)
**Goal**: Backend skeleton with database and basic CRUD

| Task | Est. | Tests |
|------|------|-------|
| Project setup (monorepo, pyproject.toml, package.json) | 3h | — |
| SQLAlchemy models + Alembic migrations | 4h | test_schemas.py |
| CRUD operations for coins | 4h | test_crud.py |
| Basic FastAPI routes (list, detail, create, update, delete) | 4h | test_coins_api.py |
| CSV import from your data | 4h | test_import.py |
| **Subtotal** | **19h** | |

**Deliverable**: Import your 110 coins, accessible via `/api/coins`

---

### Phase 2: Relational Data (Week 2)
**Goal**: References, provenance, images backend

| Task | Est. | Tests |
|------|------|-------|
| CoinReference model + endpoints | 3h | ✓ |
| ProvenanceEvent model + endpoints | 3h | ✓ |
| CoinImage model + upload handling | 4h | ✓ |
| CoinTag model + tagging | 2h | ✓ |
| Mint vocabulary + autocomplete endpoint | 2h | ✓ |
| Update CSV import to parse references | 2h | ✓ |
| **Subtotal** | **16h** | |

**Deliverable**: Full relational data model, references parsed from CSV

---

### Phase 3: Search & LLM (Week 3)
**Goal**: Faceted search + LLM integration

| Task | Est. | Tests |
|------|------|-------|
| Query builder with all filter params | 4h | ✓ |
| Pagination + sorting | 2h | ✓ |
| Full-text search on descriptions | 3h | ✓ |
| Stats endpoints (by ruler, metal, period) | 3h | ✓ |
| Claude service module | 2h | ✓ |
| Parse listing endpoint | 3h | test_llm_api.py |
| Natural language → filters | 3h | ✓ |
| Legend expansion endpoint | 1h | ✓ |
| **Subtotal** | **21h** | |

**Deliverable**: Filter by any combination, paste auction listing → structured data

---

### Phase 4: React Foundation (Week 4)
**Goal**: React app shell with routing and data fetching

| Task | Est. | Tests |
|------|------|-------|
| Vite + React + TypeScript setup | 2h | — |
| Tailwind + shadcn/ui installation | 2h | — |
| TanStack Query + Zustand setup | 2h | — |
| API client (Axios/fetch wrapper) | 2h | — |
| App shell (Header, Sidebar, routing) | 4h | — |
| Theme provider (dark/light mode) | 1h | — |
| Type definitions from backend schemas | 2h | — |
| **Subtotal** | **15h** | |

**Deliverable**: Empty app shell with navigation, theme toggle

---

### Phase 5: Core UI Components (Week 5)
**Goal**: Collection browsing and coin detail views

| Task | Est. | Tests |
|------|------|-------|
| CoinCard component | 3h | — |
| CoinGrid + CoinTable views | 4h | — |
| CoinFilters sidebar | 4h | — |
| Filter store (Zustand) | 2h | — |
| Collection page (list view) | 4h | — |
| CoinDetail page with tabs | 6h | — |
| Image gallery component | 3h | — |
| **Subtotal** | **26h** | |

**Deliverable**: Browse collection, view coin details

---

### Phase 6: Forms & Mutations (Week 6)
**Goal**: Create, edit, delete coins

| Task | Est. | Tests |
|------|------|-------|
| CoinForm component (multi-section) | 8h | — |
| React Hook Form + Zod validation | 3h | — |
| Add/Edit coin pages | 4h | — |
| Reference editor (inline add/remove) | 3h | — |
| Provenance timeline editor | 3h | — |
| Image upload with drag-drop | 4h | — |
| Delete confirmation dialog | 1h | — |
| Toast notifications (Sonner) | 1h | — |
| **Subtotal** | **27h** | |

**Deliverable**: Full CRUD from UI

---

### Phase 7: LLM Features & Import (Week 7)
**Goal**: AI-powered features and data import

| Task | Est. | Tests |
|------|------|-------|
| Natural language search bar | 3h | — |
| Parse listing dialog | 4h | — |
| Legend expander component | 2h | — |
| Import wizard (upload, map columns, preview) | 6h | — |
| Export (CSV, JSON) | 2h | ✓ |
| **Subtotal** | **17h** | |

**Deliverable**: Paste auction listing → pre-filled form, import CSV

---

### Phase 8: Polish & Deploy (Week 8)
**Goal**: Production-ready

| Task | Est. | Tests |
|------|------|-------|
| Stats dashboard with charts (Recharts) | 6h | — |
| Command palette (Cmd+K) | 3h | — |
| Keyboard navigation | 2h | — |
| Loading skeletons + error states | 3h | — |
| Responsive design fixes | 3h | — |
| Docker + docker-compose | 2h | — |
| Caddy reverse proxy config | 1h | — |
| Documentation | 2h | — |
| **Subtotal** | **22h** | |

**Deliverable**: `docker-compose up` → polished working app

---

### Total Estimates

| Phase | Hours |
|-------|-------|
| Foundation (Backend) | 19h |
| Relational Data | 16h |
| Search & LLM | 21h |
| React Foundation | 15h |
| Core UI Components | 26h |
| Forms & Mutations | 27h |
| LLM Features & Import | 17h |
| Polish & Deploy | 22h |
| **Total** | **~163h** |

At ~20h/week side project pace: **8 weeks**  
At focused sprint pace: **4-5 weeks**

---

## 9. CI/CD Configuration

```yaml
# .github/workflows/ci.yml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Install uv
        uses: astral-sh/setup-uv@v4
        
      - name: Set up Python
        run: uv python install 3.12
        
      - name: Install dependencies
        run: uv sync --dev
        
      - name: Lint with ruff
        run: uv run ruff check .
        
      - name: Type check with mypy
        run: uv run mypy app
        
      - name: Run tests
        run: uv run pytest --cov=app --cov-report=xml --cov-fail-under=95
        
      - name: Upload coverage
        uses: codecov/codecov-action@v4
        with:
          file: backend/coverage.xml
          flags: backend

  frontend-test:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      
      - name: Install dependencies
        run: npm ci
      
      - name: Lint
        run: npm run lint
      
      - name: Type check
        run: npm run typecheck
      
      - name: Build
        run: npm run build

  docker:
    needs: [backend-test, frontend-test]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Build Docker image
        run: docker-compose build
        
      - name: Test Docker image
        run: |
          docker-compose up -d
          sleep 10
          curl -f http://localhost:8000/api/health
          curl -f http://localhost:3000
          docker-compose down
```

### Docker Configuration

```yaml
# docker-compose.yml
version: '3.8'

services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    volumes:
      - ./backend/data:/app/data
      - ./uploads:/app/uploads
    environment:
      - DATABASE_URL=sqlite:///./data/coinstack.db
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:80"
    depends_on:
      - backend
    environment:
      - VITE_API_URL=http://localhost:8000

  # Optional: Caddy for HTTPS in production
  caddy:
    image: caddy:2-alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./Caddyfile:/etc/caddy/Caddyfile
      - caddy_data:/data
      - caddy_config:/config
    depends_on:
      - backend
      - frontend
    profiles:
      - production

volumes:
  caddy_data:
  caddy_config:
```

```dockerfile
# backend/Dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies
RUN uv sync --frozen --no-dev

# Copy application
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini .

# Run migrations and start server
CMD ["sh", "-c", "uv run alembic upgrade head && uv run uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=builder /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

```nginx
# frontend/nginx.conf
server {
    listen 80;
    server_name localhost;
    root /usr/share/nginx/html;
    index index.html;

    # SPA routing - serve index.html for all routes
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Proxy API requests to backend
    location /api {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Proxy image uploads
    location /uploads {
        proxy_pass http://backend:8000;
    }
}

---

## 10. Success Criteria

| Criterion | Metric |
|-----------|--------|
| Backend test coverage | ≥95% |
| All tests pass | ✓ |
| CSV import | 110 coins imported correctly |
| Search works | "Augustus denarius" returns expected coins |
| LLM parsing | Auction text → valid structured data |
| API performance | List endpoint <200ms, detail <100ms |
| Frontend build | No TypeScript errors, production build succeeds |
| Lighthouse score | Performance >80, Accessibility >90 |
| Docker | `docker-compose up` succeeds, all services healthy |
| Responsive | Usable on mobile (375px+) |

---

## 11. Frontend Package Configuration

```json
// frontend/package.json
{
  "name": "coinstack-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "lint": "eslint . --ext ts,tsx --report-unused-disable-directives --max-warnings 0",
    "typecheck": "tsc --noEmit",
    "preview": "vite preview"
  },
  "dependencies": {
    "@hookform/resolvers": "^3.3.4",
    "@radix-ui/react-dialog": "^1.0.5",
    "@radix-ui/react-dropdown-menu": "^2.0.6",
    "@radix-ui/react-label": "^2.0.2",
    "@radix-ui/react-select": "^2.0.0",
    "@radix-ui/react-slider": "^1.1.2",
    "@radix-ui/react-slot": "^1.0.2",
    "@radix-ui/react-tabs": "^1.0.4",
    "@radix-ui/react-tooltip": "^1.0.7",
    "@tanstack/react-query": "^5.28.4",
    "axios": "^1.6.8",
    "class-variance-authority": "^0.7.0",
    "clsx": "^2.1.0",
    "cmdk": "^1.0.0",
    "date-fns": "^3.6.0",
    "framer-motion": "^11.0.24",
    "lucide-react": "^0.363.0",
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-dropzone": "^14.2.3",
    "react-hook-form": "^7.51.2",
    "react-router-dom": "^6.22.3",
    "recharts": "^2.12.4",
    "sonner": "^1.4.41",
    "tailwind-merge": "^2.2.2",
    "tailwindcss-animate": "^1.0.7",
    "zod": "^3.22.4",
    "zustand": "^4.5.2"
  },
  "devDependencies": {
    "@types/node": "^20.11.30",
    "@types/react": "^18.2.67",
    "@types/react-dom": "^18.2.22",
    "@typescript-eslint/eslint-plugin": "^7.3.1",
    "@typescript-eslint/parser": "^7.3.1",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.19",
    "eslint": "^8.57.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.6",
    "postcss": "^8.4.38",
    "tailwindcss": "^3.4.1",
    "typescript": "^5.4.3",
    "vite": "^5.2.6"
  }
}
```

---

## 12. Future Enhancements (Post-MVP)

| Feature | Priority | Effort | Notes |
|---------|----------|--------|-------|
| **PWA Support** | High | 4h | Offline access, installable |
| **Multi-user auth** | Medium | 12h | Clerk or Auth.js |
| **Price tracking** | Medium | 16h | Integrate auction results API |
| **Semantic search** | Medium | 8h | Vector embeddings with pgvector |
| **Die study tools** | Low | 24h | Visual comparison, linking |
| **IIIF image viewer** | Low | 8h | High-res zoom, annotations |
| **Mobile app** | Low | 40h | React Native or Capacitor |
| **Public portfolio** | Low | 12h | Shareable collection view |
| **Batch image upload** | Medium | 4h | Drag folder, auto-match to coins |
| **Price alerts** | Low | 8h | Notify when type appears at auction |
| **Collection comparison** | Low | 12h | Compare with major collections |
| **AI coin grading assist** | Medium | 16h | Grade suggestion from images |

---

*Document generated January 2025. Update as implementation progresses.*
