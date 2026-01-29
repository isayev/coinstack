# Data Model Reference

> **Complete Schema:** For the full schema with all constraints, see [`backend/SCHEMA.md`](../../backend/SCHEMA.md).
>
> This document provides V2 Clean Architecture data layer reference with ORM models and query patterns.

---

## Architecture Overview

### Domain Entities vs ORM Models

**CRITICAL**: V2 Clean Architecture strictly separates domain entities from ORM models.

```
Domain Layer (src/domain/)
  ├── coin.py          # Coin dataclass (NO database dependencies)
  ├── auction.py       # AuctionLot dataclass
  ├── series.py        # Series dataclass
  └── vocab.py         # VocabTerm dataclass

Infrastructure Layer (src/infrastructure/persistence/)
  ├── orm.py           # CoinModel, CoinImageModel, AuctionDataModel (SQLAlchemy)
  ├── models_vocab.py  # VocabTermModel, CoinVocabAssignmentModel
  └── models_series.py # SeriesModel, SeriesSlotModel, SeriesMembershipModel
```

**Domain Entities**:
- Pure Python dataclasses (no SQLAlchemy imports)
- Business logic and validation
- Used by use cases and domain services
- Example: `Coin`, `AuctionLot`, `Series`, `VocabTerm`

**ORM Models**:
- SQLAlchemy models with `Mapped[T]` syntax
- Database persistence layer
- Converted to/from domain entities by repositories
- Example: `CoinModel`, `AuctionDataModel`, `SeriesModel`

**Repository Pattern**:
```python
# Repository converts between ORM and domain
class SqlAlchemyCoinRepository:
    def get_by_id(self, coin_id: int) -> Optional[Coin]:
        orm_coin = self.session.query(CoinModel).options(
            selectinload(CoinModel.images)  # Eager load
        ).filter(CoinModel.id == coin_id).first()

        return self._to_domain(orm_coin)  # ORM → Domain

    def save(self, coin: Coin) -> Coin:
        orm_coin = self._to_orm(coin)  # Domain → ORM
        merged = self.session.merge(orm_coin)
        self.session.flush()  # NOT commit()
        return self._to_domain(merged)
```

---

## Entity Relationship Diagram

```mermaid
erDiagram
    CoinModel ||--o{ CoinImageModel : "has"
    CoinModel ||--o{ CoinReferenceModel : "has"
    CoinModel ||--o{ ProvenanceEventModel : "has"
    CoinModel ||--o| AuctionDataModel : "linked to"
    CoinModel ||--o{ SeriesMembershipModel : "member of"
    CoinModel }o--o| VocabTermModel : "issuer"
    CoinModel }o--o| VocabTermModel : "mint"
    CoinModel }o--o| VocabTermModel : "denomination"
    CoinModel }o--o| VocabTermModel : "dynasty"
    CoinModel }o--o{ MonogramModel : "has"

    SeriesModel ||--o{ SeriesSlotModel : "has"
    SeriesModel ||--o{ SeriesMembershipModel : "has"
    SeriesModel }o--o| VocabTermModel : "canonical definition"

    SeriesSlotModel ||--o{ SeriesMembershipModel : "filled by"

    VocabTermModel ||--o{ CoinVocabAssignmentModel : "assigned to"

    CoinModel {
        int id PK
        string category
        string metal
        decimal weight_g nullable  # Optional (e.g. slabbed coins cannot be weighed)
        decimal diameter_mm
        decimal thickness_mm
        int die_axis
        string issuer
        int issuer_id FK
        int issuer_term_id FK_vocab
        string mint
        int mint_id FK
        int mint_term_id FK_vocab
        int year_start
        int year_end
        string script
        int reign_start
        int reign_end
        string grading_state
        string grade
        string acquisition_url
        string provenance_notes
        string rarity
        string issue_status
        decimal specific_gravity
        string obverse_die_id
        string reverse_die_id
        string secondary_treatments JSON
        string find_spot
        date find_date
        datetime created_at
        datetime updated_at
    }

    CoinImageModel {
        int id PK
        int coin_id FK
        string url
        string image_type
        bool is_primary
    }

    AuctionDataModel {
        int id PK
        int coin_id FK
        string url
        string source
        decimal hammer_price
        string issuer
        string mint
    }

    VocabTermModel {
        int id PK
        string vocab_type
        string canonical_name
        string nomisma_uri
        string term_metadata JSON
    }

    CoinVocabAssignmentModel {
        int id PK
        int coin_id FK
        int vocab_term_id FK
        string field_name
        string raw_value
        float confidence
        string method
        string status
    }

    MonogramModel {
        int id PK
        string label
        string image_url
        string vector_data
    }

    SeriesModel {
        int id PK
        string name
        string slug
        string series_type
        int target_count
        bool is_complete
        int canonical_vocab_id FK
    }

    SeriesSlotModel {
        int id PK
        int series_id FK
        int slot_number
        string name
        string status
        int priority
    }

    SeriesMembershipModel {
        int id PK
        int series_id FK
        int coin_id FK
        int slot_id FK
    }
```

---

## Core Tables (V2)

### `coins_v2` (CoinModel)

Central coin entity using SQLAlchemy 2.0 `Mapped[T]` syntax.

**Issuer vs portrait subject:** The **issuer** (ruling authority under whom the coin was minted) is stored in `issuer` / `issuer_id` / `issuer_term_id`. The **portrait subject** is the person, deity, or object actually depicted on the obverse; it often differs from the issuer (e.g. empress, deified predecessor, DIVVS ANTONINVS). When different, store it in `portrait_subject` (free text). Cards and detail pages show both: issuer as primary title, portrait subject when present and different.

**ORM Model** (`src/infrastructure/persistence/orm.py`):

```python
from typing import Optional, List
from decimal import Decimal
from datetime import date, datetime
from sqlalchemy import Integer, String, Numeric, Date, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column
from src.infrastructure.persistence.models import Base

class CoinModel(Base):
    __tablename__ = "coins_v2"

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Classification (indexed for filtering)
    category: Mapped[str] = mapped_column(String, index=True)
    metal: Mapped[str] = mapped_column(String, index=True)

    # Physical Dimensions; weight_g optional (e.g. slabbed coins)
    weight_g: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    diameter_mm: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    die_axis: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Attribution
    issuer: Mapped[str] = mapped_column(String)
    issuer_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("issuers.id"), nullable=True
    )
    issuer_term_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("vocab_terms.id"), nullable=True
    )

    mint: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    mint_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("mints.id"), nullable=True
    )
    mint_term_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("vocab_terms.id"), nullable=True
    )

    year_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    year_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Grading
    grading_state: Mapped[str] = mapped_column(String, index=True)
    grade: Mapped[str] = mapped_column(String)
    grade_service: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    certification_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Acquisition (optional)
    acquisition_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    acquisition_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    acquisition_source: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    acquisition_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Design
    obverse_legend: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    obverse_description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    reverse_legend: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    reverse_description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    exergue: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Denomination and portrait subject (attribution extensions)
    denomination: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Denarius, Aureus, etc.
    portrait_subject: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Person/deity on obverse when different from issuer

    # Collection Management
    storage_location: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    personal_notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # -------------------------------------------------------------------------
    # Research Grade Extensions (V2.1)
    # -------------------------------------------------------------------------
    
    # Production & Authenticity
    issue_status: Mapped[str] = mapped_column(String, default="official", index=True) 
    # Values: 'official', 'fourree', 'imitation', 'barbarous', 'modern_fake'
    
    # Metrology
    specific_gravity: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    
    # Die Linking
    obverse_die_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    reverse_die_id: Mapped[Optional[str]] = mapped_column(String, nullable=True, index=True)
    
    # Structured Secondary Treatments (Countermarks, bankers marks, etc - JSON)
    secondary_treatments: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    # Find Data
    find_spot: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    find_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # -------------------------------------------------------------------------
    # Extended V1 Fields (restored from migration)
    # -------------------------------------------------------------------------
    # Script/Language
    script: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)  # Latin, Greek
    
    # Chronology (ruler reign dates - different from mint year)
    reign_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)  # Year (negative for BC)
    reign_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    dating_certainty: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # BROAD, NARROW, EXACT
    is_circa: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=False)
    
    # Provenance
    provenance_notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # Auction history
    
    # Physical characteristics
    surface_issues: Mapped[Optional[str]] = mapped_column(String, nullable=True)  # JSON array
    thickness_mm: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    orientation: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Classification
    series: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sub_category: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Mint details
    officina: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # Mint workshop
    
    # Design symbols
    obverse_symbols: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    reverse_symbols: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Rarity and value
    rarity: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # common, scarce, rare, etc.
    rarity_notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Condition notes
    style_notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    toning_description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    eye_appeal: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    
    # Timestamps
    created_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    updated_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    
    # -------------------------------------------------------------------------
    # Advanced Numismatic Fields (Phase 2 - Comprehensive Cataloging)
    # -------------------------------------------------------------------------
    
    # Iconography and design details (JSON arrays)
    obverse_iconography: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    reverse_iconography: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    control_marks: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Mint marks and control symbols
    mintmark: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    field_marks: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Die study
    die_state: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)  # early, middle, late
    die_match_notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Republican coinage
    moneyer: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    
    # Edge details
    edge_type: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)  # plain, reeded, lettered
    edge_inscription: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Attribution confidence
    attribution_confidence: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    attribution_notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Conservation history
    cleaning_history: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    conservation_notes: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    
    # Market value tracking
    market_value: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    market_value_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # LLM-Generated Fields
    obverse_legend_expanded: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    reverse_legend_expanded: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    historical_significance: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    catalog_description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    condition_observations: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    llm_enriched_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    llm_suggested_design: Mapped[Optional[str]] = mapped_column(Text, nullable=True)   # JSON: obverse_legend, reverse_legend, exergue, obverse_description, reverse_description, *_expanded
    llm_suggested_attribution: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON: issuer, mint, denomination, year_start, year_end

    # Relationships (eager load with selectinload)
    images: Mapped[List["CoinImageModel"]] = relationship(
        back_populates="coin",
        cascade="all, delete-orphan"
    )
    auction_data: Mapped[Optional["AuctionDataModel"]] = relationship(
        back_populates="coin",
        uselist=False
    )
    references: Mapped[List["CoinReferenceModel"]] = relationship(
        back_populates="coin",
        cascade="all, delete-orphan"
    )
    provenance_events: Mapped[List["ProvenanceEventModel"]] = relationship(
        back_populates="coin",
        cascade="all, delete-orphan"
    )
    monograms: Mapped[List["MonogramModel"]] = relationship(
        secondary="coin_monograms", 
        back_populates="coins"
    )

    # V3 Vocab relationships
    issuer_vocab: Mapped[Optional["VocabTermModel"]] = relationship(
        "src.infrastructure.persistence.models_vocab.VocabTermModel",
        foreign_keys=[issuer_term_id]
    )
    mint_vocab: Mapped[Optional["VocabTermModel"]] = relationship(
        "src.infrastructure.persistence.models_vocab.VocabTermModel",
        foreign_keys=[mint_term_id]
    )
```

**Domain Entity** (`src/domain/coin.py`):

```python
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from decimal import Decimal
from datetime import date, datetime
from enum import Enum

@dataclass
class Coin:
    """Coin aggregate root - NO database dependencies."""
    id: Optional[int]
    
    # Classification
    category: str
    metal: str
    
    # Physical Dimensions
    weight_g: Decimal
    diameter_mm: Decimal
    thickness_mm: Optional[Decimal]
    die_axis: Optional[int]
    
    # Attribution
    issuer: str
    mint: Optional[str]
    year_start: Optional[int]
    year_end: Optional[int]
    
    # Script/Language
    script: Optional[str]  # Latin, Greek, etc.
    
    # Chronology (ruler reign dates)
    reign_start: Optional[int]
    reign_end: Optional[int]
    dating_certainty: Optional[str]  # BROAD, NARROW, EXACT
    is_circa: Optional[bool]
    
    # Grading
    grading_state: str
    grade: str
    grade_service: Optional[str]
    certification_number: Optional[str]
    
    # Acquisition
    acquisition_price: Optional[Decimal]
    acquisition_date: Optional[date]
    acquisition_source: Optional[str]
    acquisition_url: Optional[str]
    
    # Design
    obverse_legend: Optional[str]
    obverse_description: Optional[str]
    obverse_symbols: Optional[str]
    reverse_legend: Optional[str]
    reverse_description: Optional[str]
    reverse_symbols: Optional[str]
    exergue: Optional[str]
    
    # Classification extras
    series: Optional[str]
    sub_category: Optional[str]
    officina: Optional[str]  # Mint workshop
    orientation: Optional[str]
    
    # Provenance & History
    provenance_notes: Optional[str]  # Auction/collection history
    
    # Rarity & Value
    rarity: Optional[str]  # common, scarce, rare, very_rare, extremely_rare, unique
    rarity_notes: Optional[str]
    
    # Condition notes
    surface_issues: Optional[str]  # JSON array of issues
    style_notes: Optional[str]
    toning_description: Optional[str]
    eye_appeal: Optional[str]
    
    # Storage & Organization
    storage_location: Optional[str]
    personal_notes: Optional[str]
    
    # Timestamps
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    
    # Research Grade Extensions (V2.1)
    issue_status: str = "official" # official, fourree, imitation
    die_info: Optional['DieInfo'] = None
    monograms: List['Monogram'] = field(default_factory=list)
    secondary_treatments: Optional[List[Dict[str, Any]]] = None # JSON structure
    find_data: Optional['FindData'] = None
    
    # Related Entities
    images: List["CoinImage"] = field(default_factory=list)

    # ... validation logic ...
```

**Key Differences**:
- **Domain**: Pure dataclass, business logic, no SQLAlchemy
- **ORM**: SQLAlchemy `Mapped[T]`, relationships, database mapping

---

### `coin_images_v2` (CoinImageModel)

**ORM Model**:

```python
class CoinImageModel(Base):
    __tablename__ = "coin_images_v2"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    coin_id: Mapped[int] = mapped_column(Integer, ForeignKey("coins_v2.id"))
    url: Mapped[str] = mapped_column(String)
    image_type: Mapped[str] = mapped_column(String)  # obverse, reverse
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationship
    coin: Mapped["CoinModel"] = relationship(back_populates="images")
```

**Domain Entity**:

```python
@dataclass
class CoinImage:
    """Coin image value object."""
    id: Optional[int]
    coin_id: int
    url: str
    image_type: str  # obverse, reverse, combined
    is_primary: bool
```

---

### `auction_data_v2` (AuctionDataModel)

**ORM Model**:

```python
class AuctionDataModel(Base):
    __tablename__ = "auction_data_v2"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    coin_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("coins_v2.id"), nullable=True
    )

    # URL is unique key
    url: Mapped[str] = mapped_column(String, unique=True, index=True)
    source: Mapped[str] = mapped_column(String)  # Heritage, CNG
    sale_name: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    lot_number: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Financials
    hammer_price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    estimate_low: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    estimate_high: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    currency: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Attribution
    issuer: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    mint: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    year_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    year_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Physical
    weight_g: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 3), nullable=True
    )
    diameter_mm: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )

    # Descriptions
    title: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    grade: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Images (JSON string)
    primary_image_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    additional_images: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Metadata
    scraped_at: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # Relationship
    coin: Mapped[Optional["CoinModel"]] = relationship(back_populates="auction_data")
```

**Domain Entity**:

```python
@dataclass
class AuctionLot:
    """Auction lot data from scrapers."""
    id: Optional[int]
    url: str
    source: str
    sale_name: Optional[str]
    lot_number: Optional[str]
    hammer_price: Optional[Decimal]
    estimate_low: Optional[Decimal]
    estimate_high: Optional[Decimal]
    currency: Optional[str]
    issuer: Optional[str]
    mint: Optional[str]
    year_start: Optional[int]
    year_end: Optional[int]
    weight_g: Optional[Decimal]
    diameter_mm: Optional[Decimal]
    title: Optional[str]
    description: Optional[str]
    grade: Optional[str]
    primary_image_url: Optional[str]
    additional_images: List[str] = None
    scraped_at: Optional[date] = None
```

---

### `enrichment_jobs` (EnrichmentJobModel)

Stores progress and results for catalog bulk-enrich jobs. Used by `POST /api/catalog/bulk-enrich` and `GET /api/catalog/job/{job_id}`.

**ORM Model** (`src/infrastructure/persistence/orm.py`):

- `id` (UUID string, PK), `status` (queued/running/completed/failed), `total`, `progress`, `updated`, `conflicts`, `not_found`, `errors`, `result_summary` (JSON), `error_message`, `started_at`, `completed_at`, `created_at`

---

## Vocabulary Tables (V3)

### `vocab_terms` (VocabTermModel)

Unified controlled vocabulary system (`src/infrastructure/persistence/models_vocab.py`).

**ORM Model**:

```python
class VocabTermModel(Base):
    """
    Unified vocabulary term.

    Stores all vocabulary types (issuer, mint, denomination, dynasty, canonical_series)
    in a single table with type discrimination via vocab_type column.
    """
    __tablename__ = "vocab_terms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    vocab_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    canonical_name: Mapped[str] = mapped_column(String(200), nullable=False)
    nomisma_uri: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    term_metadata: Mapped[Optional[str]] = mapped_column(
        "metadata", Text, nullable=True
    )  # JSON string
    created_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
```

**Domain Entity**:

```python
@dataclass
class VocabTerm:
    """Controlled vocabulary term."""
    id: Optional[int]
    vocab_type: str  # issuer, mint, denomination, dynasty
    canonical_name: str
    nomisma_uri: Optional[str]
    metadata: Optional[dict]  # Type-specific data
    created_at: Optional[str]
```

**Vocab Types**:
- `issuer`: Issuing authorities (Augustus, Tiberius, etc.)
- `mint`: Mint locations (Rome, Lugdunum, etc.)
- `denomination`: Coin types (Denarius, Aureus, etc.)
- `dynasty`: Dynasties (Julio-Claudian, Flavian, etc.)
- `canonical_series`: Standard series definitions (RIC types)

---

### `coin_vocab_assignments` (CoinVocabAssignmentModel)

Audit trail for vocabulary assignments.

**ORM Model**:

```python
class CoinVocabAssignmentModel(Base):
    """
    Tracks vocabulary term assignments to coins.

    Items with status='pending_review' appear in review queue.
    """
    __tablename__ = "coin_vocab_assignments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    coin_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("coins_v2.id"), nullable=False, index=True
    )
    field_name: Mapped[str] = mapped_column(String(50), nullable=False)
    raw_value: Mapped[str] = mapped_column(Text, nullable=False)
    vocab_term_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("vocab_terms.id"), nullable=True
    )
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    method: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    # Method: 'exact', 'fts', 'nomisma', 'llm', 'manual'
    status: Mapped[str] = mapped_column(String(20), default="assigned", index=True)
    # Status: 'assigned', 'pending_review', 'approved', 'rejected'
    assigned_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    reviewed_at: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    vocab_term: Mapped[Optional["VocabTermModel"]] = relationship("VocabTermModel")
```

---

### `vocab_cache` (VocabCacheModel)

Simple key-value cache for vocabulary operations.

**ORM Model**:

```python
class VocabCacheModel(Base):
    """
    Cache for search results (1hr TTL) and API responses (1yr TTL).
    """
    __tablename__ = "vocab_cache"

    cache_key: Mapped[str] = mapped_column(String(200), primary_key=True)
    data: Mapped[str] = mapped_column(Text, nullable=False)  # JSON string
    expires_at: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
```

---

### `monograms` (MonogramModel)

Storage for monogram definitions (Research Grade V2.1).

**ORM Model**:

```python
class MonogramModel(Base):
    __tablename__ = "monograms"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    label: Mapped[str] = mapped_column(String, index=True) # e.g. "Price 123"
    image_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    vector_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # SVG path or data
    
    # Relationship back to coins via association table
    coins: Mapped[List["CoinModel"]] = relationship(secondary="coin_monograms", back_populates="monograms")
```

---

### `coin_monograms` (Association Table)

Many-to-many link between coins and monograms.

```python
coin_monograms = Table(
    "coin_monograms",
    Base.metadata,
    Column("coin_id", Integer, ForeignKey("coins_v2.id"), primary_key=True),
    Column("monogram_id", Integer, ForeignKey("monograms.id"), primary_key=True),
)
```

---

## Series Tables

### `series` (SeriesModel)

Series/collection management (`src/infrastructure/persistence/models_series.py`).

**ORM Model**:

```python
class SeriesModel(Base):
    __tablename__ = "series"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    description: Mapped[Optional[str]] = mapped_column(Text)
    series_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # Types: ruler, type, catalog, custom
    category: Mapped[Optional[str]] = mapped_column(String(50))

    target_count: Mapped[Optional[int]] = mapped_column(Integer)
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    completion_date: Mapped[Optional[datetime]] = mapped_column(DateTime)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    # Link to canonical definition in vocab_terms
    canonical_vocab_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("vocab_terms.id"), nullable=True
    )

    # Relationships
    slots: Mapped[List["SeriesSlotModel"]] = relationship(
        back_populates="series",
        cascade="all, delete-orphan"
    )
    memberships: Mapped[List["SeriesMembershipModel"]] = relationship(
        back_populates="series",
        cascade="all, delete-orphan"
    )
    canonical_definition: Mapped[Optional["VocabTermModel"]] = relationship(
        "src.infrastructure.persistence.models_vocab.VocabTermModel"
    )
```

**Domain Entity**:

```python
@dataclass
class Series:
    """Series/collection grouping."""
    id: Optional[int]
    name: str
    slug: str
    description: Optional[str]
    series_type: str
    category: Optional[str]
    target_count: Optional[int]
    is_complete: bool
    completion_date: Optional[datetime]
    created_at: datetime
    canonical_vocab_id: Optional[int]
    slots: List["SeriesSlot"] = None
    memberships: List["SeriesMembership"] = None
```

---

### `series_slots` (SeriesSlotModel)

Predefined slots within a series.

**ORM Model**:

```python
class SeriesSlotModel(Base):
    __tablename__ = "series_slots"

    id: Mapped[int] = mapped_column(primary_key=True)
    series_id: Mapped[int] = mapped_column(
        ForeignKey("series.id", ondelete='CASCADE'), nullable=False
    )
    slot_number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)

    status: Mapped[str] = mapped_column(String(20), default="empty", index=True)
    # Status: empty, filled, duplicate

    priority: Mapped[int] = mapped_column(Integer, default=5)

    series: Mapped["SeriesModel"] = relationship(back_populates="slots")
    memberships: Mapped[List["SeriesMembershipModel"]] = relationship(
        back_populates="slot",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        CheckConstraint('slot_number > 0', name='check_slot_number'),
        UniqueConstraint('series_id', 'slot_number', name='uq_series_slot_number'),
    )
```

---

### `series_memberships` (SeriesMembershipModel)

Links coins to series and slots.

**ORM Model**:

```python
class SeriesMembershipModel(Base):
    __tablename__ = "series_memberships"

    id: Mapped[int] = mapped_column(primary_key=True)
    series_id: Mapped[int] = mapped_column(
        ForeignKey("series.id", ondelete='CASCADE'), nullable=False
    )
    coin_id: Mapped[int] = mapped_column(
        ForeignKey("coins_v2.id", ondelete='CASCADE'), nullable=False
    )
    slot_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("series_slots.id", ondelete='SET NULL')
    )

    assigned_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    series: Mapped["SeriesModel"] = relationship(back_populates="memberships")
    slot: Mapped[Optional["SeriesSlotModel"]] = relationship(back_populates="memberships")
```

---

## SQLAlchemy 2.0 Patterns

### ORM Syntax (MANDATORY)

**Rule**: Always use `Mapped[T]` + `mapped_column()` syntax.

```python
# ✅ CORRECT (SQLAlchemy 2.0)
class CoinModel(Base):
    __tablename__ = "coins_v2"

    # Required field (non-nullable)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    category: Mapped[str] = mapped_column(String, index=True)
    weight_g: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    # Optional field (nullable)
    mint: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    acquisition_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # One-to-Many relationship
    images: Mapped[List["CoinImageModel"]] = relationship(
        back_populates="coin",
        cascade="all, delete-orphan"
    )

    # Many-to-One relationship
    issuer_vocab: Mapped[Optional["VocabTermModel"]] = relationship(
        "VocabTermModel",
        foreign_keys=[issuer_term_id]
    )

# ❌ WRONG (Old Column syntax)
class CoinModel(Base):
    __tablename__ = "coins_v2"

    id = Column(Integer, primary_key=True)  # ❌ NO type hints
    category = Column(String, index=True)    # ❌ Missing Mapped[T]
    mint = Column(String, nullable=True)     # ❌ Not Optional[str]
```

**Why this matters**:
- Type safety and IDE autocomplete
- mypy compatibility
- Modern SQLAlchemy 2.0 best practices
- Consistency with V2 codebase

---

### Query Patterns (Prevent N+1)

**Rule**: Always use `selectinload()` for relationships.

```python
from sqlalchemy.orm import selectinload

# ✅ CORRECT (Eager loading)
def get_coin_with_images(coin_id: int) -> Optional[Coin]:
    orm_coin = self.session.query(CoinModel).options(
        selectinload(CoinModel.images),        # Eager load images
        selectinload(CoinModel.references)     # Eager load references
    ).filter(CoinModel.id == coin_id).first()

    return self._to_domain(orm_coin)

# ❌ WRONG (Lazy loading causes N+1)
def get_coin_with_images(coin_id: int) -> Optional[Coin]:
    orm_coin = self.session.query(CoinModel).filter(
        CoinModel.id == coin_id
    ).first()  # ❌ Images not loaded

    # Accessing orm_coin.images triggers N queries
    return self._to_domain(orm_coin)
```

**Why this matters**:
- **Without eager loading**: 1 query for coin + N queries for images = O(n)
- **With eager loading**: 1 query for coin + 1 query for all images = O(1)
- Performance: 10-100x faster with large collections

---

### Transaction Management

**Rule**: Repositories use `flush()`, never `commit()`.

```python
# ✅ CORRECT (Repository uses flush)
class SqlAlchemyCoinRepository:
    def save(self, coin: Coin) -> Coin:
        orm_coin = self._to_orm(coin)
        merged = self.session.merge(orm_coin)
        self.session.flush()  # ✅ Get ID, but don't commit
        return self._to_domain(merged)

# get_db() dependency handles commit automatically
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

# ❌ WRONG (Repository commits)
class SqlAlchemyCoinRepository:
    def save(self, coin: Coin) -> Coin:
        orm_coin = self._to_orm(coin)
        merged = self.session.merge(orm_coin)
        self.session.commit()  # ❌ Breaks transaction boundaries
        return self._to_domain(merged)
```

**Why this matters**:
- Multiple repository calls in one request = one transaction
- Exceptions automatically roll back ALL changes
- Clean separation: repositories handle data, dependency handles transactions

---

## Common Query Patterns

### Get Coin with Relationships

```python
from sqlalchemy.orm import selectinload

stmt = (
    self.session.query(CoinModel)
    .options(
        selectinload(CoinModel.images),
        selectinload(CoinModel.references),
        selectinload(CoinModel.provenance_events),
        selectinload(CoinModel.issuer_vocab),
        selectinload(CoinModel.mint_vocab)
    )
    .filter(CoinModel.id == coin_id)
)
orm_coin = stmt.first()
```

### Filter Coins by Multiple Criteria

```python
stmt = self.session.query(CoinModel).options(
    selectinload(CoinModel.images)  # Always eager load
)

if category:
    stmt = stmt.filter(CoinModel.category == category)
if metal:
    stmt = stmt.filter(CoinModel.metal == metal)
if issuer:
    stmt = stmt.filter(CoinModel.issuer.ilike(f"%{issuer}%"))
if year_start:
    stmt = stmt.filter(CoinModel.year_end >= year_start)
if year_end:
    stmt = stmt.filter(CoinModel.year_start <= year_end)

stmt = stmt.order_by(CoinModel.year_start.desc())
stmt = stmt.offset(skip).limit(limit)

coins = stmt.all()
```

### Search Vocabulary Terms

```python
from sqlalchemy import or_

stmt = (
    self.session.query(VocabTermModel)
    .filter(VocabTermModel.vocab_type == vocab_type)
    .filter(
        or_(
            VocabTermModel.canonical_name.ilike(f"%{query}%"),
            VocabTermModel.nomisma_uri.ilike(f"%{query}%")
        )
    )
    .limit(10)
)
terms = stmt.all()
```

### Get Series with Coins

```python
stmt = (
    self.session.query(SeriesModel)
    .options(
        selectinload(SeriesModel.slots),
        selectinload(SeriesModel.memberships)
    )
    .filter(SeriesModel.slug == series_slug)
)
series = stmt.first()
```

---

## Enum Values

> **Full enums:** See [`backend/SCHEMA.md`](../../backend/SCHEMA.md) for complete enum definitions.

### Category
```
greek | celtic | republic | imperial | provincial | judaean | byzantine | migration | pseudo_roman | other
```

### Metal
```
gold | electrum | silver | billon | potin | orichalcum | bronze | copper | lead | ae | uncertain
```

### IssueStatus
```
official | fourree | imitation | barbarous | modern_fake | tooling_altered
```

### Script
```
Latin | Greek | Greek?
```

### DateCertainty
```
BROAD | NARROW | EXACT
```

### Orientation
```
OBVERSE_UP | REVERSE_UP
```

### Rarity
```
common | scarce | rare | very_rare | extremely_rare | unique
```

### DieState
```
early | middle | late | worn
```

### EdgeType
```
plain | reeded | lettered | decorated
```

### AttributionConfidence
```
certain | probable | possible | uncertain
```

### GradeService
```
ngc | pcgs | self | dealer
```

### ImageType
```
obverse | reverse | edge | slab | detail | combined | other
```

### SeriesType
```
ruler | type | catalog | custom
```

### SlotStatus
```
empty | filled | duplicate
```

### VocabType
```
issuer | mint | denomination | dynasty | canonical_series
```

### AssignmentMethod
```
exact | fts | nomisma | llm | manual
```

### AssignmentStatus
```
assigned | pending_review | approved | rejected
```

---

## Database Configuration

### Import Paths (V2)

```python
# ✅ CORRECT (V2 imports)
from src.infrastructure.persistence.database import get_db, init_db
from src.infrastructure.persistence.orm import CoinModel, CoinImageModel
from src.infrastructure.persistence.models_vocab import VocabTermModel
from src.infrastructure.persistence.models_series import SeriesModel

# ❌ WRONG (V1 imports)
from app.database import get_db  # ❌ V1 path
from app.models import Coin        # ❌ V1 path
```

### Database URL

```python
DATABASE_URL = "sqlite:///./coinstack_v2.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite-specific
    echo=False  # Set True for SQL logging
)
```

### Session Management

```python
# In FastAPI endpoints
from src.infrastructure.persistence.database import get_db
from sqlalchemy.orm import Session

@router.get("/coins/{coin_id}")
def get_coin(coin_id: int, db: Session = Depends(get_db)):
    # Session automatically commits on success, rolls back on error
    coin = db.query(CoinModel).filter(CoinModel.id == coin_id).first()
    return coin
```

---

## Critical Rules

### Port Configuration (MANDATORY)
- Backend: Port 8000
- Frontend: Port 3000
- Never increment ports

### Database Safety (MANDATORY)
- REQUIRED: Timestamped backup to `backend/backups/` BEFORE schema changes
- Format: `coinstack_YYYYMMDD_HHMMSS.db`

**Existing DBs and `weight_g` nullable:** If your database was created before `weight_g` was made optional, run the one-off migration (backup is automatic): from `backend/`, `uv run python scripts/migrations/make_weight_g_nullable.py`. New databases created via `create_all()` get the nullable column automatically.

### Architecture Rules (MANDATORY)
- Domain entities have NO SQLAlchemy imports
- ORM models use `Mapped[T]` + `mapped_column()` syntax
- Repositories use `flush()` NOT `commit()`
- Always use `selectinload()` for relationships
- Use cases depend on interfaces (Protocols), not implementations

---

**Previous:** [04-FRONTEND-MODULES.md](04-FRONTEND-MODULES.md) - Frontend reference
**Next:** [06-DATA-FLOWS.md](06-DATA-FLOWS.md) - Data flows and sequences