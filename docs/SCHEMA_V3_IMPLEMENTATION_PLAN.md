# CoinStack Schema V3 Implementation Plan

> **Version**: 3.0
> **Created**: 2026-01-31
> **Status**: Ready for Implementation

---

## Executive Summary

This document outlines the phased migration from CoinStack Schema V2.1 to V3, designed to support world-class numismatic functionality including:

- Enhanced attribution for complex coin types (Greek, Byzantine, Provincial)
- Comprehensive grading history and TPG integration
- Multi-source rarity assessments with grade-conditional tracking
- Flexible catalog reference system with concordance support
- Centralized LLM enrichment architecture
- Market tracking, wishlists, and price alerts
- User-defined collections and sub-collections

---

## Migration Phases Overview

| Phase | Name | Tables | Est. Effort | Dependencies |
|-------|------|--------|-------------|--------------|
| **1** | Core Numismatic Enhancements | coins_v2 (ALTER) | 1-2 days | None |
| **2** | Grading & Rarity System | 3 new tables | 2-3 days | Phase 1 |
| **3** | Reference System Enhancements | 2 new tables, 1 ALTER | 1-2 days | None |
| **4** | LLM Architecture Refactor | 4 new tables | 3-4 days | None |
| **5** | Market Tracking & Wishlists | 6 new tables | 3-4 days | Phase 1 |
| **6** | Collections & Sub-collections | 2 new tables | 1-2 days | None |

**Total Estimated Effort**: 11-17 days

---

## Phase 1: Core Numismatic Enhancements

### Purpose
Extend `coins_v2` table with fields for world-class numismatic cataloging.

### New Columns

```sql
-- Attribution enhancements
secondary_authority TEXT           -- Greek magistrates, provincial governors
secondary_authority_term_id FK     -- Link to vocab_terms
authority_type TEXT                -- 'magistrate', 'satrap', 'dynast', 'strategos'
co_ruler TEXT                      -- Byzantine/Imperial co-rulers
co_ruler_term_id FK                -- Link to vocab_terms
portrait_relationship TEXT         -- 'consort', 'heir', 'divus/diva', 'commemorative'
moneyer_gens TEXT                  -- Republican moneyer family (gens)

-- Physical enhancements
weight_standard TEXT               -- 'attic', 'denarius_early', 'antoninianus'
expected_weight_g NUMERIC(10,3)    -- Theoretical weight for type
flan_shape TEXT                    -- 'round', 'scyphate', 'irregular'
flan_type TEXT                     -- 'cast', 'struck', 'hammered'
flan_notes TEXT                    -- Edge cracks, planchet flaws

-- Secondary treatments (structured)
is_overstrike BOOLEAN              -- Is this an overstrike?
undertype_visible TEXT             -- Description of undertype traces
undertype_attribution TEXT         -- Attribution of host coin
has_test_cut BOOLEAN               -- Prüfhieb present
test_cut_count INTEGER             -- Number of test cuts
has_bankers_marks BOOLEAN          -- Banker's marks present
has_graffiti BOOLEAN               -- Ancient graffiti
graffiti_description TEXT          -- Graffiti transcription
was_mounted BOOLEAN                -- Mounted as jewelry
mount_evidence TEXT                -- Loop removed, bezel marks, etc.

-- Tooling/repairs
tooling_extent TEXT                -- 'none', 'minor', 'moderate', 'significant'
tooling_details TEXT               -- Specific tooling description
has_ancient_repair BOOLEAN         -- Ancient repair present
ancient_repairs TEXT               -- Plug, filled hole, etc.

-- Centering
centering TEXT                     -- 'well-centered', 'slightly_off', 'off_center'
centering_notes TEXT               -- Detailed centering description

-- Die study enhancements
obverse_die_state TEXT             -- Separate from die_state
reverse_die_state TEXT             -- 'fresh', 'early', 'middle', 'late', 'broken'
die_break_description TEXT         -- Cud at 2:00, crack from neck to legend

-- Grading TPG enhancements
grade_numeric INTEGER              -- 50, 58, 62, 65 (PCGS/NGC scale)
grade_designation TEXT             -- 'Fine Style', 'Choice', 'Gem'
has_star_designation BOOLEAN       -- NGC ★ grade
photo_certificate BOOLEAN          -- NGC Photo Certificate
verification_url TEXT              -- NGC/PCGS cert lookup URL

-- Chronology
date_period_notation TEXT          -- Human-readable: "c. 150-100 BC"
emission_phase TEXT                -- "First Issue", "Reform Coinage"
```

### Migration File
`backend/alembic/versions/20260201_phase1_core_numismatic.py`

### Data Migration
- No data migration required (all new columns are nullable)
- Existing `secondary_treatments` JSON can be parsed to populate boolean flags

### Domain Model Updates
- Extend `Coin` dataclass in `backend/src/domain/coin.py`
- Add new fields to `Attribution`, create `SecondaryTreatments` value object

### ORM Updates
- Add columns to `CoinModel` in `backend/src/infrastructure/persistence/orm.py`

### API Updates
- Extend `CoinResponse` Pydantic model
- Update serialization in `v2.py` router

### Frontend Updates
- Extend `CoinSchema` in `frontend/src/domain/schemas.ts`
- Add UI fields in `CoinForm` steps

---

## Phase 2: Grading & Rarity System

### Purpose
Comprehensive TPG tracking with history and multi-source rarity assessments.

### New Tables

#### `grading_history`
Track complete grading lifecycle (raw → slabbed → regraded).

```sql
CREATE TABLE grading_history (
    id INTEGER PRIMARY KEY,
    coin_id INTEGER NOT NULL REFERENCES coins_v2(id) ON DELETE CASCADE,

    -- Grading state
    grading_state TEXT NOT NULL,
    grade TEXT,
    grade_service TEXT,
    certification_number TEXT,
    strike_quality TEXT,
    surface_quality TEXT,
    grade_numeric INTEGER,
    designation TEXT,
    has_star BOOLEAN DEFAULT FALSE,
    photo_cert BOOLEAN DEFAULT FALSE,
    verification_url TEXT,

    -- Event tracking
    event_type TEXT NOT NULL,  -- 'initial', 'crossover', 'regrade', 'crack_out'
    graded_date DATE,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    submitter TEXT,
    turnaround_days INTEGER,
    grading_fee NUMERIC(8,2),
    notes TEXT,

    -- Ordering
    sequence_order INTEGER NOT NULL DEFAULT 0,
    is_current BOOLEAN NOT NULL DEFAULT FALSE
);
```

#### `rarity_assessments`
Multi-source rarity tracking with grade-conditional support.

```sql
CREATE TABLE rarity_assessments (
    id INTEGER PRIMARY KEY,
    coin_id INTEGER NOT NULL REFERENCES coins_v2(id) ON DELETE CASCADE,

    -- Classification
    rarity_code TEXT NOT NULL,      -- C, S, R1-R5, RR, RRR, UNIQUE
    rarity_system TEXT NOT NULL,    -- 'RIC', 'census', 'market_frequency'

    -- Source attribution
    source_type TEXT NOT NULL,      -- 'catalog', 'census_data', 'auction_analysis'
    source_name TEXT,
    source_url TEXT,
    source_date DATE,

    -- Grade-conditional
    grade_range_low TEXT,
    grade_range_high TEXT,
    grade_conditional_notes TEXT,

    -- Census data
    census_total INTEGER,
    census_this_grade INTEGER,
    census_finer INTEGER,
    census_date DATE,

    -- Metadata
    confidence TEXT DEFAULT 'medium',
    notes TEXT,
    is_primary BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `census_snapshots`
Track NGC/PCGS population over time.

```sql
CREATE TABLE census_snapshots (
    id INTEGER PRIMARY KEY,
    coin_id INTEGER NOT NULL REFERENCES coins_v2(id) ON DELETE CASCADE,

    service TEXT NOT NULL,          -- 'NGC', 'PCGS'
    snapshot_date DATE NOT NULL,
    total_graded INTEGER NOT NULL,
    grade_breakdown TEXT,           -- JSON: {"VF": 10, "EF": 5}
    coins_at_grade INTEGER,
    coins_finer INTEGER,
    percentile NUMERIC(5,2),
    catalog_reference TEXT,
    notes TEXT
);
```

### Migration File
`backend/alembic/versions/20260202_phase2_grading_rarity.py`

### Data Migration
```sql
-- Populate initial grading_history from current state
INSERT INTO grading_history (coin_id, grading_state, grade, grade_service, ...)
SELECT id, grading_state, grade, grade_service, ...
FROM coins_v2 WHERE grading_state IS NOT NULL;

-- Migrate rarity to rarity_assessments
INSERT INTO rarity_assessments (coin_id, rarity_code, rarity_system, ...)
SELECT id, rarity, 'catalog', ...
FROM coins_v2 WHERE rarity IS NOT NULL;
```

### Domain Model Updates
- Create `GradingHistoryEntry` entity
- Create `RarityAssessment` entity
- Create `CensusSnapshot` value object

### API Endpoints
```
GET  /api/v2/coins/{id}/grading-history
POST /api/v2/coins/{id}/grading-history
GET  /api/v2/coins/{id}/rarity
POST /api/v2/coins/{id}/rarity
```

---

## Phase 3: Reference System Enhancements

### Purpose
Flexible catalog reference system with concordance and external links.

### Schema Changes

#### Extend `reference_types`
```sql
ALTER TABLE reference_types ADD COLUMN sng_volume TEXT;
ALTER TABLE reference_types ADD COLUMN number_numeric INTEGER;
ALTER TABLE reference_types ADD COLUMN publication_year INTEGER;
ALTER TABLE reference_types ADD COLUMN rarity_code TEXT;

CREATE INDEX idx_ref_number_numeric ON reference_types(system, number_numeric);
```

#### New: `reference_concordance`
Cross-reference linking (RIC 207 = RSC 112 = BMC 298).

```sql
CREATE TABLE reference_concordance (
    id INTEGER PRIMARY KEY,
    concordance_group_id TEXT NOT NULL,  -- UUID grouping equivalent refs
    reference_type_id INTEGER NOT NULL REFERENCES reference_types(id),
    confidence REAL DEFAULT 1.0,
    source TEXT,                         -- 'ocre', 'user', 'literature'
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(concordance_group_id, reference_type_id)
);
```

#### New: `external_catalog_links`
Links to OCRE, Nomisma, CRRO, RPC Online.

```sql
CREATE TABLE external_catalog_links (
    id INTEGER PRIMARY KEY,
    reference_type_id INTEGER NOT NULL REFERENCES reference_types(id),
    catalog_source TEXT NOT NULL,        -- 'ocre', 'nomisma', 'crro', 'rpc_online'
    external_id TEXT NOT NULL,
    external_url TEXT,
    external_data TEXT,                  -- JSON metadata from source
    last_synced_at TIMESTAMP,
    UNIQUE(reference_type_id, catalog_source)
);
```

#### Extend `coin_references`
```sql
ALTER TABLE coin_references ADD COLUMN attribution_confidence TEXT;
ALTER TABLE coin_references ADD COLUMN catalog_rarity_note TEXT;
ALTER TABLE coin_references ADD COLUMN disagreement_note TEXT;
```

### Migration File
`backend/alembic/versions/20260203_phase3_references.py`

### Domain Model Updates
- Extend `CatalogReference` value object
- Create `Concordance` entity
- Create `ExternalCatalogLink` value object

---

## Phase 4: LLM Architecture Refactor

### Purpose
Centralize LLM enrichments with versioning, review workflow, and quality tracking.

### New Tables

#### `llm_enrichments`
Replaces 11 inline columns with structured, versioned storage.

```sql
CREATE TABLE llm_enrichments (
    id INTEGER PRIMARY KEY,
    coin_id INTEGER NOT NULL REFERENCES coins_v2(id) ON DELETE CASCADE,

    -- Capability
    capability TEXT NOT NULL,
    capability_version INTEGER NOT NULL DEFAULT 1,

    -- Model provenance
    model_id TEXT NOT NULL,
    model_version TEXT,

    -- Content
    input_hash TEXT NOT NULL,
    input_snapshot TEXT,
    output_content TEXT NOT NULL,
    raw_response TEXT,

    -- Quality
    confidence REAL NOT NULL,
    needs_review BOOLEAN DEFAULT FALSE,
    quality_flags TEXT,

    -- Cost
    cost_usd REAL DEFAULT 0.0,
    input_tokens INTEGER,
    output_tokens INTEGER,
    cached BOOLEAN DEFAULT FALSE,

    -- Review workflow
    review_status TEXT DEFAULT 'pending',
    reviewed_by TEXT,
    reviewed_at TIMESTAMP,
    review_notes TEXT,

    -- Lifecycle
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    superseded_by INTEGER REFERENCES llm_enrichments(id),
    request_id TEXT,
    batch_job_id TEXT,

    UNIQUE(coin_id, capability, input_hash, review_status)
);
```

#### `llm_prompt_templates`
Database-managed prompts for versioning and A/B testing.

```sql
CREATE TABLE llm_prompt_templates (
    id INTEGER PRIMARY KEY,
    capability TEXT NOT NULL,
    version INTEGER NOT NULL,

    system_prompt TEXT NOT NULL,
    user_template TEXT NOT NULL,
    parameters TEXT,
    requires_vision BOOLEAN DEFAULT FALSE,
    output_schema TEXT,

    variant_name TEXT DEFAULT 'default',
    traffic_weight REAL DEFAULT 1.0,

    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deprecated_at TIMESTAMP,
    notes TEXT,

    UNIQUE(capability, version, variant_name)
);
```

#### `llm_feedback`
Quality feedback loop.

```sql
CREATE TABLE llm_feedback (
    id INTEGER PRIMARY KEY,
    enrichment_id INTEGER NOT NULL REFERENCES llm_enrichments(id) ON DELETE CASCADE,
    feedback_type TEXT NOT NULL,
    field_path TEXT,
    original_value TEXT,
    corrected_value TEXT,
    user_id TEXT,
    feedback_notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `llm_usage_daily`
Aggregated analytics.

```sql
CREATE TABLE llm_usage_daily (
    date TEXT NOT NULL,
    capability TEXT NOT NULL,
    model_id TEXT NOT NULL,

    request_count INTEGER DEFAULT 0,
    cache_hits INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0,
    total_cost_usd REAL DEFAULT 0.0,
    total_input_tokens INTEGER DEFAULT 0,
    total_output_tokens INTEGER DEFAULT 0,
    avg_confidence REAL,
    review_approved INTEGER DEFAULT 0,
    review_rejected INTEGER DEFAULT 0,
    avg_latency_ms REAL,

    PRIMARY KEY(date, capability, model_id)
);
```

### Migration File
`backend/alembic/versions/20260204_phase4_llm_architecture.py`

### Data Migration
```sql
-- Migrate existing LLM data to llm_enrichments
INSERT INTO llm_enrichments (coin_id, capability, output_content, ...)
SELECT id, 'context_generate', llm_analysis_sections, ...
FROM coins_v2 WHERE llm_analysis_sections IS NOT NULL;

-- Similar for other LLM columns...
```

### Domain Model Updates
- Create `LLMEnrichment` entity
- Create `PromptTemplate` entity
- Update `ILLMService` interface

### Service Updates
- Refactor `LLMService` to use new tables
- Implement dual-write during transition
- Add review workflow endpoints

---

## Phase 5: Market Tracking & Wishlists

### Purpose
Price monitoring, valuations, alerts, and acquisition wishlists.

### New Tables

#### `market_prices`
Aggregate pricing by attribution.

```sql
CREATE TABLE market_prices (
    id INTEGER PRIMARY KEY,
    attribution_key TEXT NOT NULL UNIQUE,
    catalog_ref TEXT,
    denomination TEXT,
    metal TEXT,
    last_updated TIMESTAMP
);
```

#### `market_data_points`
Individual price observations.

```sql
CREATE TABLE market_data_points (
    id INTEGER PRIMARY KEY,
    market_price_id INTEGER NOT NULL REFERENCES market_prices(id),
    price NUMERIC(12,2) NOT NULL,
    currency TEXT DEFAULT 'USD',
    source TEXT NOT NULL,              -- 'auction_realized', 'dealer_asking'
    date DATE NOT NULL,
    grade TEXT,
    auction_house TEXT,
    lot_url TEXT,
    confidence TEXT DEFAULT 'medium'
);
```

#### `coin_valuations`
Valuation snapshots per coin.

```sql
CREATE TABLE coin_valuations (
    id INTEGER PRIMARY KEY,
    coin_id INTEGER NOT NULL REFERENCES coins_v2(id) ON DELETE CASCADE,
    valuation_date DATE NOT NULL,
    purchase_price NUMERIC(12,2),
    purchase_date DATE,
    current_market_value NUMERIC(12,2),
    market_confidence TEXT,
    comparable_count INTEGER,
    price_trend_12mo REAL,
    gain_loss_usd NUMERIC(12,2),
    gain_loss_pct REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### `price_alerts`
User alert configurations.

```sql
CREATE TABLE price_alerts (
    id INTEGER PRIMARY KEY,
    attribution_key TEXT,
    coin_id INTEGER REFERENCES coins_v2(id),
    wishlist_id INTEGER,               -- FK added after wishlist_items created

    trigger_type TEXT NOT NULL,
    threshold_value NUMERIC(12,2),
    threshold_pct REAL,

    status TEXT DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    triggered_at TIMESTAMP,
    expires_at TIMESTAMP,
    notification_sent BOOLEAN DEFAULT FALSE,
    notes TEXT
);
```

#### `wishlist_items`
Acquisition targets.

```sql
CREATE TABLE wishlist_items (
    id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,

    -- Targeting criteria
    issuer TEXT,
    mint TEXT,
    year_start INTEGER,
    year_end INTEGER,
    denomination TEXT,
    catalog_ref TEXT,

    -- Preferences
    min_grade TEXT,
    max_price NUMERIC(12,2),
    priority INTEGER DEFAULT 2,

    -- Status
    status TEXT DEFAULT 'wanted',
    series_slot_id INTEGER REFERENCES series_slots(id),
    acquired_coin_id INTEGER REFERENCES coins_v2(id),
    acquired_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP,
    notes TEXT
);
```

#### `wishlist_matches`
Matched auction lots.

```sql
CREATE TABLE wishlist_matches (
    id INTEGER PRIMARY KEY,
    wishlist_item_id INTEGER NOT NULL REFERENCES wishlist_items(id) ON DELETE CASCADE,

    match_type TEXT NOT NULL,
    match_id TEXT NOT NULL,
    match_url TEXT,

    title TEXT NOT NULL,
    description TEXT,
    grade TEXT,
    price NUMERIC(12,2),
    currency TEXT DEFAULT 'USD',

    match_score REAL,
    confidence TEXT,
    auction_date DATE,
    is_below_budget BOOLEAN,
    is_below_market BOOLEAN,
    value_score REAL,

    notified BOOLEAN DEFAULT FALSE,
    dismissed BOOLEAN DEFAULT FALSE,
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Migration File
`backend/alembic/versions/20260205_phase5_market_wishlist.py`

### Domain Model Updates
- Create `MarketPrice`, `MarketDataPoint` entities
- Create `CoinValuation` value object
- Create `PriceAlert` entity
- Create `WishlistItem`, `WishlistMatch` entities

### Domain Services
- `ValuationService` - Calculate coin/portfolio valuations
- `PriceAlertService` - Monitor and trigger alerts
- `WishlistMatchingService` - Match auctions to wishlists

### API Endpoints
```
GET  /api/v2/market/valuation/{coin_id}
GET  /api/v2/market/portfolio
POST /api/v2/market/prices
GET  /api/v2/market/trends

GET  /api/v2/alerts
POST /api/v2/alerts
PUT  /api/v2/alerts/{id}
DELETE /api/v2/alerts/{id}

GET  /api/v2/wishlist
POST /api/v2/wishlist
PUT  /api/v2/wishlist/{id}
DELETE /api/v2/wishlist/{id}
GET  /api/v2/wishlist/matches
POST /api/v2/wishlist/scan
```

---

## Phase 6: Collections & Sub-collections

### Purpose
User-defined collection groupings with smart filters.

### New Tables

#### `collections`
Collection definitions.

```sql
CREATE TABLE collections (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    collection_type TEXT DEFAULT 'custom',  -- 'custom', 'smart'
    smart_filter TEXT,                       -- JSON filter criteria
    cover_image_url TEXT,
    display_order INTEGER,
    is_favorite BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);
```

#### `collection_coins`
Many-to-many linking.

```sql
CREATE TABLE collection_coins (
    collection_id INTEGER NOT NULL REFERENCES collections(id) ON DELETE CASCADE,
    coin_id INTEGER NOT NULL REFERENCES coins_v2(id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    position INTEGER,
    notes TEXT,
    PRIMARY KEY(collection_id, coin_id)
);
```

### Migration File
`backend/alembic/versions/20260206_phase6_collections.py`

### Domain Model Updates
- Create `Collection` entity
- Create `CollectionMembership` value object

### API Endpoints
```
GET  /api/v2/collections
POST /api/v2/collections
GET  /api/v2/collections/{id}
PUT  /api/v2/collections/{id}
DELETE /api/v2/collections/{id}
POST /api/v2/collections/{id}/coins/{coin_id}
DELETE /api/v2/collections/{id}/coins/{coin_id}
```

---

## Implementation Checklist

### Pre-Migration
- [ ] Full database backup to `backend/backups/`
- [ ] Verify Alembic configuration
- [ ] Review migration SQL in SQLite

### Phase 1
- [ ] Create migration file
- [ ] Run migration
- [ ] Update `CoinModel` ORM
- [ ] Update `Coin` domain entity
- [ ] Update `CoinMapper`
- [ ] Update API response models
- [ ] Update frontend schemas
- [ ] Test CRUD operations

### Phase 2
- [ ] Create migration file
- [ ] Run migration + data migration
- [ ] Create `GradingHistory` ORM model
- [ ] Create `RarityAssessment` ORM model
- [ ] Create domain entities
- [ ] Create repositories
- [ ] Add API endpoints
- [ ] Update frontend with new components

### Phase 3
- [ ] Create migration file
- [ ] Run migration
- [ ] Extend `ReferenceType` model
- [ ] Create `Concordance` model
- [ ] Create `ExternalCatalogLink` model
- [ ] Update reference parsers
- [ ] Add concordance API

### Phase 4
- [ ] Create migration file
- [ ] Run migration
- [ ] Create `LLMEnrichment` model
- [ ] Create `PromptTemplate` model
- [ ] Refactor `LLMService` for dual-write
- [ ] Migrate existing data
- [ ] Add review workflow API
- [ ] Update frontend enrichment UI

### Phase 5
- [ ] Create migration file
- [ ] Run migration
- [ ] Create market tracking models
- [ ] Create wishlist models
- [ ] Implement domain services
- [ ] Add all API endpoints
- [ ] Create frontend pages (Portfolio, Wishlist, Alerts)

### Phase 6
- [ ] Create migration file
- [ ] Run migration
- [ ] Create collection models
- [ ] Add API endpoints
- [ ] Create frontend collection management UI

### Post-Migration
- [ ] Update `docs/ai-guide/05-DATA-MODEL.md`
- [ ] Update `docs/ai-guide/07-API-REFERENCE.md`
- [ ] Run full test suite
- [ ] Performance testing with larger dataset
- [ ] Create backup after successful migration

---

## Rollback Strategy

Each migration includes a `downgrade()` function. If issues occur:

```bash
cd backend

# Rollback specific phase
uv run alembic downgrade -1

# Rollback to baseline
uv run alembic downgrade 892810d42bbe

# Check current revision
uv run alembic current
```

**Important:** Always backup before migration:
```bash
.\backup.ps1
```

---

## Testing Strategy

### Unit Tests
- Domain entity validation
- Value object immutability
- Repository interface compliance

### Integration Tests
- Migration up/down cycles
- Data migration accuracy
- API endpoint responses

### Frontend Tests
- Schema validation with Zod
- Form field rendering
- API client type safety

---

## Timeline

| Week | Phases | Focus |
|------|--------|-------|
| 1 | 1, 3 | Core schema + references |
| 2 | 2 | Grading & rarity system |
| 3 | 4 | LLM architecture |
| 4 | 5 | Market tracking & wishlists |
| 5 | 6 | Collections + testing |

---

**Document Version**: 1.0
**Last Updated**: 2026-01-31
