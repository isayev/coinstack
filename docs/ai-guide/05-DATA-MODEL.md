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
  ├── orm.py           # CoinModel, CoinImageModel, AuctionDataModel, ProvenanceEventModel (SQLAlchemy)
  ├── models_vocab.py  # VocabTermModel, CoinVocabAssignmentModel
  └── models_series.py # SeriesModel, SeriesSlotModel, SeriesMembershipModel
```

**Repository Pattern (with Mapper)**:
```python
# Repository converts between ORM and domain via CoinMapper
class SqlAlchemyCoinRepository:
    def get_by_id(self, coin_id: int) -> Optional[Coin]:
        orm_coin = self.session.query(CoinModel).options(
            selectinload(CoinModel.images)  # Eager load
        ).filter(CoinModel.id == coin_id).first()

        return CoinMapper.to_domain(orm_coin) if orm_coin else None

    def save(self, coin: Coin) -> Coin:
        orm_coin = CoinMapper.to_model(coin)
        merged = self.session.merge(orm_coin)
        self.session.flush()  # NOT commit()
        return CoinMapper.to_domain(merged)
```

### Domain Entity: AuctionLot

**CRITICAL**: The `AuctionLot` domain entity (`src/domain/auction.py`) has specific field names that differ from common assumptions. When writing services that use `AuctionLot`, reference this table:

| Field | Type | Notes |
|-------|------|-------|
| `source` | `str` | Auction house name (NOT `auction_house`) |
| `lot_id` | `str` | Unique lot identifier |
| `url` | `str` | Auction URL |
| `lot_number` | `Optional[str]` | Display lot number |
| `auction_date` | `Optional[date]` | Sale date (NOT `sale_date`) |
| `hammer_price` | `Optional[Decimal]` | Final sale price (NOT `realized_price`) |
| `estimate_low` | `Optional[Decimal]` | Low estimate |
| `estimate_high` | `Optional[Decimal]` | High estimate |
| `currency` | `str` | Default "USD" |
| `issuer` | `Optional[str]` | Issuing authority |
| `mint` | `Optional[str]` | Mint location |
| `year_start` | `Optional[int]` | Start year (NOT `date_start`) |
| `year_end` | `Optional[int]` | End year (NOT `date_end`) |
| `grade` | `Optional[str]` | Grade string |
| `description` | `Optional[str]` | Full description text |
| `primary_image_url` | `Optional[str]` | Main image (NOT `image_urls`) |
| `additional_images` | `List[str]` | Additional image URLs |

**Missing fields**: AuctionLot does NOT have:
- `denomination` - extract from `description`
- `references` - extract from `description`
- `title` - construct from `issuer`/`mint`

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
    CoinModel ||--o{ CountermarkModel : "has"

    SeriesModel ||--o{ SeriesSlotModel : "has"
    SeriesModel ||--o{ SeriesMembershipModel : "has"
    SeriesModel }o--o| VocabTermModel : "canonical definition"

    SeriesSlotModel ||--o{ SeriesMembershipModel : "filled by"

    VocabTermModel ||--o{ CoinVocabAssignmentModel : "assigned to"
    
    CoinReferenceModel }o--o| ReferenceTypeModel : "refers to"
    ProvenanceEventModel |o--o| AuctionDataModel : "linked to"

    CoinModel {
        int id PK
        string category
        string metal
        decimal weight_g nullable  # Numeric(10,3)
        decimal diameter_mm
        decimal thickness_mm
        int die_axis               # Check(0-12)
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
```

---

## Core Tables (V2)

### `coins_v2` (CoinModel)

Central coin entity using SQLAlchemy 2.0 `Mapped[T]` syntax.

**ORM Model** (`src/infrastructure/persistence/orm.py`):

```python
class CoinModel(Base):
    __tablename__ = "coins_v2"
    
    # Constraints
    __table_args__ = (
        CheckConstraint('die_axis >= 0 AND die_axis <= 12', name='check_die_axis_range'),
    )

    # Primary Key
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    # Classification
    category: Mapped[str] = mapped_column(String(50), index=True)
    metal: Mapped[str] = mapped_column(String(50), index=True)

    # Physical Dimensions
    # Precision 10,3 for accurate numismatic weights
    weight_g: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3), nullable=True)
    diameter_mm: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    die_axis: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    thickness_mm: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)

    # Attribution
    issuer: Mapped[str] = mapped_column(String(100))
    mint: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    year_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True, index=True)
    year_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    
    # V3 Vocab FKs
    issuer_term_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("vocab_terms.id"), nullable=True)
    mint_term_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("vocab_terms.id"), nullable=True)
    denomination_term_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("vocab_terms.id"), nullable=True)
    dynasty_term_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("vocab_terms.id"), nullable=True)

    # Grading
    grading_state: Mapped[str] = mapped_column(String(20), index=True)
    grade: Mapped[str] = mapped_column(String(20))
    grade_service: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    certification_number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)

    # Acquisition
    acquisition_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    acquisition_currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    acquisition_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    acquisition_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True, index=True)
    acquisition_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Research Grade Extensions (V2.1)
    issue_status: Mapped[str] = mapped_column(String(20), default="official", index=True) 
    specific_gravity: Mapped[Optional[Decimal]] = mapped_column(Numeric(5, 2), nullable=True)
    obverse_die_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    reverse_die_id: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, index=True)
    secondary_treatments: Mapped[Optional[str]] = mapped_column(Text, nullable=True) # JSON
    find_spot: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    find_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    # LLM-Generated Fields
    historical_significance: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    llm_enriched_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    llm_analysis_sections: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    llm_suggested_references: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    
    # Relationships
    images: Mapped[List["CoinImageModel"]] = relationship(back_populates="coin", cascade="all, delete-orphan")
    auction_data: Mapped[Optional["AuctionDataModel"]] = relationship(back_populates="coin", uselist=False, cascade="all, delete-orphan")
    references: Mapped[List["CoinReferenceModel"]] = relationship(back_populates="coin", cascade="all, delete-orphan")
    provenance_events: Mapped[List["ProvenanceEventModel"]] = relationship(back_populates="coin", cascade="all, delete-orphan")
    monograms: Mapped[List["MonogramModel"]] = relationship(secondary=coin_monograms, back_populates="coins")
```

### `reference_types` (ReferenceTypeModel)

Stores catalog metadata (RIC, Crawford, Sear, etc.) independent of coins.

```python
class ReferenceTypeModel(Base):
    __tablename__ = "reference_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    system: Mapped[str] = mapped_column(String(20))  # ric, crawford, sear, rpc, etc.
    local_ref: Mapped[str] = mapped_column(String(100))  # canonical form e.g. "RIC I 207"
    volume: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    number: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    external_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    # Catalog-specific
    variant: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    mint: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
```

### `coin_references` (CoinReferenceModel)

Association between Coins and ReferenceTypes, with specimen-specific data.

```python
class CoinReferenceModel(Base):
    __tablename__ = "coin_references"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    coin_id: Mapped[int] = mapped_column(Integer, ForeignKey("coins_v2.id"), index=True)
    reference_type_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("reference_types.id"), nullable=True, index=True)
    
    is_primary: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=False)
    plate_coin: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True, default=False)
    
    # Citation fields
    page: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    plate: Mapped[Optional[str]] = mapped_column(String(30), nullable=True)
    notes: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
```

### `provenance_events` (ProvenanceEventModel)

Tracks ownership history (auctions, dealers, collections).

```python
class ProvenanceEventModel(Base):
    __tablename__ = "provenance_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    coin_id: Mapped[int] = mapped_column(Integer, ForeignKey("coins_v2.id"), index=True)
    
    event_type: Mapped[str] = mapped_column(String(50))  # "auction", "dealer", "collection"
    event_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    
    # Auction details
    auction_house: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sale_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True) # via sale_series/number
    lot_number: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    
    # Pricing
    hammer_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    total_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2), nullable=True)
    currency: Mapped[Optional[str]] = mapped_column(String(3), nullable=True)
    
    # Link to scraped auction data
    auction_data_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("auction_data_v2.id"), nullable=True)
```

---

## Enrichment Tables

### `enrichment_jobs` (EnrichmentJobModel)

Tracks bulk catalog enrichment job progress.

```python
class EnrichmentJobModel(Base):
    __tablename__ = "enrichment_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, index=True)  # UUID
    status: Mapped[str] = mapped_column(String(20), index=True)  # queued, running, completed, failed
    total: Mapped[int] = mapped_column(Integer, default=0)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    result_summary: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON
    updated: Mapped[int] = mapped_column(Integer, default=0)
    conflicts: Mapped[int] = mapped_column(Integer, default=0)
    not_found: Mapped[int] = mapped_column(Integer, default=0)
    errors: Mapped[int] = mapped_column(Integer, default=0)
```

---

## Schema V3 Tables (2026-02-01)

Schema V3 adds comprehensive support for world-class numismatic functionality.

### Phase 1: Core Numismatic Enhancements ✅ (coins_v2)

**Status**: Complete - Migration applied, all layers implemented

New columns added to `coins_v2` for attribution, physical characteristics, and grading:

| Category | Fields |
|----------|--------|
| **Attribution** | `secondary_authority`, `secondary_authority_term_id`, `authority_type`, `co_ruler`, `co_ruler_term_id`, `portrait_relationship`, `moneyer_gens` |
| **Physical** | `weight_standard`, `expected_weight_g`, `flan_shape`, `flan_type`, `flan_notes` |
| **Secondary Treatments** | `is_overstrike`, `undertype_visible`, `undertype_attribution`, `has_test_cut`, `test_cut_count`, `test_cut_positions`, `has_bankers_marks`, `has_graffiti`, `graffiti_description`, `was_mounted`, `mount_evidence` |
| **Tooling** | `tooling_extent`, `tooling_details`, `has_ancient_repair`, `ancient_repairs` |
| **Centering** | `centering`, `centering_notes` |
| **Die Study** | `obverse_die_state`, `reverse_die_state`, `die_break_description` |
| **TPG Grading** | `grade_numeric`, `grade_designation`, `has_star_designation`, `photo_certificate`, `verification_url` |
| **Chronology** | `date_period_notation`, `emission_phase` |
| **Phase 1.5b/c: Strike Quality** | `strike_quality_detail`, `is_double_struck`, `is_brockage`, `is_off_center`, `off_center_pct` |
| **Phase 1.5b: NGC Grades** | `ngc_strike_grade`, `ngc_surface_grade`, `is_fine_style` |

**Domain Value Objects** (`backend/src/domain/coin.py`):

```python
@dataclass(frozen=True)
class SecondaryAuthority:
    name: Optional[str] = None
    term_id: Optional[int] = None
    authority_type: Optional[str] = None  # 'magistrate', 'satrap', 'dynast', 'strategos'

@dataclass(frozen=True)
class CoRuler:
    name: Optional[str] = None
    term_id: Optional[int] = None
    portrait_relationship: Optional[str] = None  # 'consort', 'heir', 'divus', 'commemorative'

@dataclass(frozen=True)
class PhysicalEnhancements:
    weight_standard: Optional[str] = None  # 'attic', 'denarius_reformed', etc.
    expected_weight_g: Optional[Decimal] = None
    flan_shape: Optional[str] = None  # 'round', 'scyphate', 'irregular'
    flan_type: Optional[str] = None  # 'cast', 'struck', 'hammered'
    flan_notes: Optional[str] = None

@dataclass(frozen=True)
class SecondaryTreatments:
    is_overstrike: bool = False
    undertype_visible: Optional[str] = None
    undertype_attribution: Optional[str] = None
    has_test_cut: bool = False
    test_cut_count: Optional[int] = None
    test_cut_positions: Optional[str] = None
    has_bankers_marks: bool = False
    has_graffiti: bool = False
    graffiti_description: Optional[str] = None
    was_mounted: bool = False
    mount_evidence: Optional[str] = None

@dataclass(frozen=True)
class ToolingRepairs:
    tooling_extent: Optional[str] = None  # 'none', 'minor', 'moderate', 'significant'
    tooling_details: Optional[str] = None
    has_ancient_repair: bool = False
    ancient_repairs: Optional[str] = None

@dataclass(frozen=True)
class Centering:
    centering: Optional[str] = None  # 'well-centered', 'slightly_off', 'off_center'
    centering_notes: Optional[str] = None

@dataclass(frozen=True)
class DieStudyEnhancements:
    obverse_die_state: Optional[str] = None  # 'fresh', 'early', 'middle', 'late', 'broken'
    reverse_die_state: Optional[str] = None
    die_break_description: Optional[str] = None

@dataclass(frozen=True)
class GradingTPGEnhancements:
    grade_numeric: Optional[int] = None  # 50, 58, 62, 65 (PCGS/NGC scale)
    grade_designation: Optional[str] = None  # 'Fine Style', 'Choice', 'Gem'
    has_star_designation: bool = False
    photo_certificate: bool = False
    verification_url: Optional[str] = None
    # Phase 1.5b: NGC-specific fields (PCGS doesn't use 1-5 scale for ancients)
    ngc_strike_grade: Optional[int] = None  # NGC 1-5 strike grade
    ngc_surface_grade: Optional[int] = None  # NGC 1-5 surface grade
    is_fine_style: bool = False  # NGC Fine Style designation

@dataclass(frozen=True)
class ChronologyEnhancements:
    date_period_notation: Optional[str] = None  # "c. 150-100 BC"
    emission_phase: Optional[str] = None  # "First Issue", "Reform Coinage"

# --- Phase 1.5b: Countermark System & Strike Quality ---

@dataclass(frozen=True)
class Countermark:
    """Individual countermark on a coin. Supports multiple per coin."""
    id: Optional[int] = None
    coin_id: Optional[int] = None
    countermark_type: Optional[CountermarkType] = None  # revalidation, legionary, civic_symbol, etc.
    position: Optional[CountermarkPosition] = None  # obverse, reverse, edge, both_sides
    condition: Optional[CountermarkCondition] = None  # clear, partial, worn, uncertain
    punch_shape: Optional[PunchShape] = None  # Phase 1.5c: rectangular, circular, oval, etc.
    description: Optional[str] = None  # e.g., "Howgego 746", "NCAPR in rectangle"
    authority: Optional[str] = None  # Who applied it (emperor, city, legion)
    reference: Optional[str] = None  # Howgego number, GIC reference
    date_applied: Optional[str] = None
    notes: Optional[str] = None

@dataclass(frozen=True)
class StrikeQualityDetail:
    """Manufacturing characteristics and die errors."""
    detail: Optional[str] = None  # Detailed strike description
    is_double_struck: bool = False  # Die shift / double strike
    is_brockage: bool = False  # Incuse mirror image error
    is_off_center: bool = False  # Off-center strike (common)
    off_center_pct: Optional[int] = None  # Phase 1.5c: Percentage off-center (5-95%)
```

### Phase 1.5b: Countermarks Table (NEW)

**`countermarks`** - Multi-countermark support with placement tracking
```python
class CountermarkModel(Base):
    __tablename__ = "countermarks"
    id: Primary key
    coin_id: FK to coins_v2 (CASCADE)
    countermark_type: 'revalidation', 'revaluation', 'imperial_portrait',
                     'imperial_monogram', 'legionary', 'civic_symbol',
                     'royal_dynastic', 'trade_merchant', 'religious_cult', 'uncertain'
    position: 'obverse', 'reverse', 'edge', 'both_sides'
    condition: 'clear', 'partial', 'worn', 'uncertain'
    punch_shape: 'rectangular', 'circular', 'oval', 'square', 'irregular',
                 'triangular', 'star', 'uncertain'  # Phase 1.5c
    description: Text (Howgego reference, visual description)
    authority: Who applied it
    reference: Howgego number
    date_applied: When applied (if known)
    notes: Text
    created_at: Timestamp
```

**Indexes**: `ix_countermarks_coin_id`, `ix_countermarks_coin_type`

**Relationship**: `CoinModel.countermarks` (one-to-many, lazy='selectin')

**API Request/Response Models** - See `backend/src/infrastructure/web/routers/v2.py` for:
- `SecondaryAuthorityRequest/Response`
- `CoRulerRequest/Response`
- `PhysicalEnhancementsRequest/Response`
- `SecondaryTreatmentsV3Request/Response`
- `ToolingRepairsRequest/Response`
- `CenteringRequest/Response`
- `DieStudyEnhancementsRequest/Response`
- `GradingTPGEnhancementsRequest/Response`
- `ChronologyEnhancementsRequest/Response`

**Frontend Zod Schemas** - See `frontend/src/domain/schemas.ts` for corresponding TypeScript types.

### Phase 2: Grading & Rarity System

**`grading_history`** - TPG lifecycle tracking (raw → slabbed → regraded)
```python
class GradingHistoryModel(Base):
    __tablename__ = "grading_history"
    coin_id: FK to coins_v2
    grading_state, grade, grade_service, certification_number
    grade_numeric, designation, has_star, photo_cert, verification_url
    event_type: 'initial', 'crossover', 'regrade', 'crack_out'
    graded_date, turnaround_days, grading_fee
    sequence_order, is_current
```

**`rarity_assessments`** - Multi-source rarity with grade-conditional support
```python
class RarityAssessmentModel(Base):
    __tablename__ = "rarity_assessments"
    coin_id: FK to coins_v2
    rarity_code: 'C', 'S', 'R1'-'R5', 'RR', 'RRR', 'UNIQUE'
    rarity_system: 'RIC', 'catalog', 'census', 'market_frequency'
    source_type: 'catalog', 'census_data', 'auction_analysis', 'expert_opinion'
    grade_range_low, grade_range_high, grade_conditional_notes
    census_total, census_this_grade, census_finer
    is_primary, confidence
```

**`census_snapshots`** - NGC/PCGS population tracking over time

### Phase 3: Reference System Enhancements

**`reference_concordance`** - Cross-reference linking (RIC 207 = RSC 112 = BMC 298)
```python
class ReferenceConcordanceModel(Base):
    __tablename__ = "reference_concordance"
    concordance_group_id: UUID grouping equivalent references
    reference_type_id: FK to reference_types
    confidence: 0.0-1.0
    source: 'ocre', 'crro', 'user', 'literature'
```

**`external_catalog_links`** - Links to OCRE, Nomisma, CRRO, RPC Online

### Phase 4: LLM Architecture

**`llm_enrichments`** - Centralized LLM outputs with versioning and review workflow
```python
class LLMEnrichmentModel(Base):
    __tablename__ = "llm_enrichments"
    coin_id: FK to coins_v2
    capability: 'context_generate', 'attribution_suggest', 'catalog_lookup', etc.
    model_id, model_version
    input_hash, output_content, confidence
    review_status: 'pending', 'approved', 'rejected', 'revised'
    cost_usd, input_tokens, output_tokens
```

**`llm_prompt_templates`** - Database-managed prompts for A/B testing
**`llm_feedback`** - Quality feedback loop
**`llm_usage_daily`** - Aggregated analytics

### Phase 5: Market Tracking & Wishlists

**`market_prices`** - Aggregate pricing by attribution (type-level)
**`market_data_points`** - Individual price observations
**`coin_valuations`** - Valuation snapshots per coin
**`price_alerts`** - User alert configurations
**`wishlist_items`** - Acquisition targets
**`wishlist_matches`** - Matched auction lots

### Phase 6: Collections & Sub-collections

**`collections`** - Custom and smart collections
```python
class CollectionModel(Base):
    __tablename__ = "collections"
    name, description, slug
    collection_type: 'custom', 'smart', 'series', 'system'
    smart_filter: JSON filter criteria
    parent_id: FK for hierarchical organization
    coin_count, total_value
```

**`collection_coins`** - Many-to-many with ordering and metadata

---

## SQLAlchemy 2.0 Patterns

### ORM Syntax (MANDATORY)

**Rule**: Always use `Mapped[T]` + `mapped_column()` syntax.

### Query Patterns (Prevent N+1)

**Rule**: Always use `selectinload()` for relationships.

### Transaction Management

**Rule**: Repositories use `flush()`, never `commit()`.

---

**Next:** [06-DATA-FLOWS.md](06-DATA-FLOWS.md) - Data flows and sequences