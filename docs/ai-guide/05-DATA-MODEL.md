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

### Phase 1: Core Numismatic Enhancements (coins_v2)

New columns added to `coins_v2` for attribution, physical characteristics, and grading:

| Category | Fields |
|----------|--------|
| **Attribution** | `secondary_authority`, `co_ruler`, `portrait_relationship`, `authority_type`, `moneyer_gens` |
| **Physical** | `weight_standard`, `expected_weight_g`, `flan_shape`, `flan_type`, `flan_notes` |
| **Secondary Treatments** | `is_overstrike`, `undertype_visible`, `has_test_cut`, `has_bankers_marks`, `has_graffiti`, `was_mounted` |
| **Tooling** | `tooling_extent`, `tooling_details`, `has_ancient_repair`, `ancient_repairs` |
| **Centering** | `centering`, `centering_notes` |
| **Die Study** | `obverse_die_state`, `reverse_die_state`, `die_break_description` |
| **TPG Grading** | `grade_numeric`, `grade_designation`, `has_star_designation`, `photo_certificate`, `verification_url` |
| **Chronology** | `date_period_notation`, `emission_phase` |

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