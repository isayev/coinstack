# CoinStack V2 Refactoring Backlog

**Generated**: 2026-01-25
**Status**: V2 at 15% feature parity with V1
**Goal**: Achieve 100% feature parity + Clean Architecture compliance

---

## Priority 0: BLOCKERS (Must Fix Immediately)

### B1: Missing Database Tables
**Impact**: Runtime crashes on coin image/auction operations
**Effort**: 2 hours
**Files**: `backend/src/infrastructure/persistence/database.py`, `orm.py`

**Tasks**:
- [ ] Run `init_db()` to create `coin_images_v2` and `auction_data_v2` tables
- [ ] Verify tables exist with proper schema
- [ ] Add migration script to ensure idempotency

**Acceptance Criteria**:
```bash
sqlite3 backend/coinstack_v2.db ".tables" | grep -E "coin_images_v2|auction_data_v2"
```

---

### B2: Enable Foreign Key Constraints
**Impact**: Data integrity violations, orphaned records
**Effort**: 1 hour
**Files**: `backend/src/infrastructure/persistence/database.py`

**Tasks**:
- [ ] Add SQLAlchemy event listener to enable `PRAGMA foreign_keys=ON`
- [ ] Test cascade deletes work properly
- [ ] Document FK enforcement in CLAUDE.md

**Implementation**:
```python
from sqlalchemy import event

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
```

**Acceptance Criteria**:
```sql
sqlite3 backend/coinstack_v2.db "PRAGMA foreign_keys;"
-- Should return: 1
```

---

### B3: Fix Missing AuctionLot.additional_images Field
**Impact**: All scrapers crash on execution
**Effort**: 15 minutes
**Files**: `backend/src/domain/auction.py:43`

**Tasks**:
- [ ] Add field: `additional_images: List[str] = field(default_factory=list)`
- [ ] Run scraper tests to verify fix
- [ ] Update ORM model if needed

**Validation**:
```bash
python -m pytest tests/ -k scraper
```

---

### B4: Fix Coin.add_image() Primary Image Logic
**Impact**: Multiple primary images possible, breaks UI
**Effort**: 30 minutes
**Files**: `backend/src/domain/coin.py:117-127`

**Tasks**:
- [ ] Replace incomplete `pass` statement with proper logic
- [ ] Reconstruct images list when setting new primary
- [ ] Add unit test for primary image replacement

**Implementation**:
```python
def add_image(self, url: str, image_type: str, is_primary: bool = False):
    if is_primary:
        # Clear existing primary flags
        self.images = [
            CoinImage(img.url, img.image_type, False)
            for img in self.images
        ]
    self.images.append(CoinImage(url, image_type, is_primary))
```

**Test**:
```python
def test_add_primary_image_clears_existing():
    coin = Coin(...)
    coin.add_image("img1.jpg", "obverse", is_primary=True)
    coin.add_image("img2.jpg", "reverse", is_primary=True)

    primary_count = sum(1 for img in coin.images if img.is_primary)
    assert primary_count == 1
    assert coin.images[-1].is_primary
```

---

### B5: Fix Repository Field Mapping Bug
**Impact**: Silent data loss - grading service not persisted
**Effort**: 5 minutes
**Files**: `backend/src/infrastructure/repositories/coin_repository.py:172`

**Tasks**:
- [ ] Change `service=` to `grade_service=`
- [ ] Add integration test for grading persistence
- [ ] Verify existing data integrity

**Fix**:
```python
# Line 172 - BEFORE:
service=coin.grading.service.value if coin.grading.service else None,

# Line 172 - AFTER:
grade_service=coin.grading.service.value if coin.grading.service else None,
```

---

### B6: Remove Repository Transaction Commits
**Impact**: Breaks Unit of Work pattern, inconsistent behavior
**Effort**: 1 hour
**Files**: `backend/src/infrastructure/repositories/coin_repository.py:112`

**Tasks**:
- [ ] Remove `self.session.commit()` from `delete()` method
- [ ] Add transaction management to router layer or use middleware
- [ ] Standardize all repositories (no commits in repo methods)
- [ ] Document transaction boundaries in CLAUDE.md

**Implementation**:
```python
# coin_repository.py:108-114 - BEFORE:
def delete(self, coin_id: int) -> bool:
    orm_coin = self.session.get(CoinModel, coin_id)
    if orm_coin:
        self.session.delete(orm_coin)
        self.session.commit()  # ❌ REMOVE THIS
        return True
    return False

# AFTER:
def delete(self, coin_id: int) -> bool:
    orm_coin = self.session.get(CoinModel, coin_id)
    if orm_coin:
        self.session.delete(orm_coin)
        self.session.flush()  # ✅ Let caller commit
        return True
    return False
```

**Router/Middleware Addition**:
```python
# v2.py - Add transaction management
@router.delete("/{coin_id}")
def delete_coin(coin_id: int, repo: ICoinRepository = Depends(get_coin_repo),
                db: Session = Depends(get_db)):
    try:
        result = repo.delete(coin_id)
        db.commit()  # ✅ Commit at application boundary
        return {"success": result}
    except Exception as e:
        db.rollback()
        raise
```

---

## Priority 1: CRITICAL (Production Blockers)

### C1: Create Missing Database Indexes
**Impact**: Full table scans on 10K+ coins = 10-100x slower queries
**Effort**: 4 hours
**Files**: `backend/src/infrastructure/persistence/orm.py`, create migration script

**Tasks**:
- [ ] Add indexes on `coins_v2`: `issuer`, `category`, `year_start`, `acquisition_date`, `metal`
- [ ] Add indexes on `series`: `slug` (unique)
- [ ] Add indexes on `issuers`: `canonical_name` (unique), `nomisma_uri`
- [ ] Create Alembic migration or manual SQL script
- [ ] Measure query performance before/after

**Migration Script** (`backend/src/infrastructure/scripts/add_indexes.py`):
```python
from sqlalchemy import create_engine, text
from src.infrastructure.config import get_settings

def add_indexes():
    settings = get_settings()
    engine = create_engine(settings.DATABASE_URL)

    with engine.connect() as conn:
        indexes = [
            "CREATE INDEX IF NOT EXISTS ix_coins_v2_issuer ON coins_v2(issuer);",
            "CREATE INDEX IF NOT EXISTS ix_coins_v2_category ON coins_v2(category);",
            "CREATE INDEX IF NOT EXISTS ix_coins_v2_metal ON coins_v2(metal);",
            "CREATE INDEX IF NOT EXISTS ix_coins_v2_year_start ON coins_v2(year_start);",
            "CREATE INDEX IF NOT EXISTS ix_coins_v2_acquisition_date ON coins_v2(acquisition_date);",
            "CREATE INDEX IF NOT EXISTS ix_issuers_canonical_name ON issuers(canonical_name);",
            "CREATE INDEX IF NOT EXISTS ix_series_slug ON series(slug);",
        ]

        for idx_sql in indexes:
            print(f"Creating: {idx_sql}")
            conn.execute(text(idx_sql))
            conn.commit()

        print("All indexes created successfully")

if __name__ == "__main__":
    add_indexes()
```

**Acceptance Criteria**:
```sql
EXPLAIN QUERY PLAN SELECT * FROM coins_v2 WHERE issuer LIKE '%Augustus%';
-- Should show: SEARCH coins_v2 USING INDEX ix_coins_v2_issuer
```

---

### C2: Fix N+1 Query Problems
**Impact**: API response times 10-100x slower with large collections
**Effort**: 2 hours
**Files**: `backend/src/infrastructure/repositories/coin_repository.py`, `series.py` router

**Tasks**:
- [ ] Add eager loading for coin images in `get_by_id()` and `get_all()`
- [ ] Add eager loading for series slots in series list endpoint
- [ ] Add query profiling tests
- [ ] Document eager loading patterns in CLAUDE.md

**Implementation**:
```python
# coin_repository.py:65-69
from sqlalchemy.orm import selectinload

def get_by_id(self, coin_id: int) -> Optional[Coin]:
    orm_coin = self.session.query(CoinModel).options(
        selectinload(CoinModel.images)
    ).filter(CoinModel.id == coin_id).first()

    if not orm_coin:
        return None
    return self._to_domain(orm_coin)

def get_all(self, skip: int = 0, limit: int = 100,
            sort_by: Optional[str] = None, sort_dir: str = "asc") -> List[Coin]:
    query = self.session.query(CoinModel).options(
        selectinload(CoinModel.images)  # ✅ Eager load
    )
    # ... rest of method
```

```python
# series.py:50
def get_series_list(db: Session = Depends(get_db), ...):
    items = db.query(SeriesModel).options(
        selectinload(SeriesModel.slots)  # ✅ Eager load
    ).offset(skip).limit(limit).all()
    # ... rest of method
```

**Test**:
```python
def test_get_all_coins_query_count():
    """Verify N+1 queries are eliminated."""
    import sqlalchemy
    from sqlalchemy import event

    query_count = 0

    def count_queries(conn, cursor, statement, parameters, context, executemany):
        nonlocal query_count
        query_count += 1

    event.listen(engine, "before_cursor_execute", count_queries)

    repo.get_all(limit=50)

    # Should be 1 query (coins + images), not 51
    assert query_count <= 2, f"N+1 detected: {query_count} queries"
```

---

### C3: Add Missing Repository Interfaces
**Impact**: Cannot mock for testing, tight coupling to implementations
**Effort**: 3 hours
**Files**: `backend/src/domain/repositories.py`

**Tasks**:
- [ ] Create `IAuctionDataRepository` protocol
- [ ] Create `ISeriesRepository` protocol
- [ ] Create `IVocabRepository` protocol (issuers, mints)
- [ ] Update use cases to depend on interfaces
- [ ] Update dependency injection in `dependencies.py`

**Implementation**:
```python
# backend/src/domain/repositories.py

from typing import Protocol, Optional, List
from src.domain.auction import AuctionLot

class IAuctionDataRepository(Protocol):
    """Repository interface for auction data persistence."""

    def upsert(self, lot: AuctionLot, coin_id: Optional[int] = None) -> int:
        """Insert or update auction lot data. Returns auction_data_id."""
        ...

    def get_by_coin_id(self, coin_id: int) -> Optional[AuctionLot]:
        """Get auction data linked to a coin."""
        ...

    def get_by_url(self, url: str) -> Optional[AuctionLot]:
        """Get auction data by unique URL."""
        ...

    def get_comparables(self, reference_type_id: int, limit: int = 10) -> List[AuctionLot]:
        """Get comparable auction lots for price analysis."""
        ...

class ISeriesRepository(Protocol):
    """Repository interface for series/collection management."""

    def create(self, series: Series) -> Series:
        ...

    def get_by_id(self, series_id: int) -> Optional[Series]:
        ...

    def get_by_slug(self, slug: str) -> Optional[Series]:
        ...

    def list_all(self, skip: int = 0, limit: int = 100) -> List[Series]:
        ...

    def update(self, series: Series) -> Series:
        ...

    def delete(self, series_id: int) -> bool:
        ...

class IVocabRepository(Protocol):
    """Repository interface for vocabulary (issuers, mints)."""

    def get_issuer_by_id(self, issuer_id: int) -> Optional[Issuer]:
        ...

    def get_issuer_by_name(self, canonical_name: str) -> Optional[Issuer]:
        ...

    def create_issuer(self, issuer: Issuer) -> Issuer:
        ...

    def list_issuers(self, search: Optional[str] = None, skip: int = 0, limit: int = 100) -> List[Issuer]:
        ...

    # Similar methods for Mint
```

**Update Use Case**:
```python
# enrich_coin.py - BEFORE:
from src.infrastructure.repositories.auction_data_repository import SqlAlchemyAuctionDataRepository

class EnrichCoinUseCase:
    def __init__(self, coin_repo: ICoinRepository,
                 auction_repo: SqlAlchemyAuctionDataRepository, ...):  # ❌

# AFTER:
from src.domain.repositories import IAuctionDataRepository

class EnrichCoinUseCase:
    def __init__(self, coin_repo: ICoinRepository,
                 auction_repo: IAuctionDataRepository, ...):  # ✅
```

---

### C4: Replace Bare Except Clauses
**Impact**: Hides critical errors, difficult debugging
**Effort**: 1 hour
**Files**: `agora/parser.py:86,168`, `cng/scraper.py:55`, `biddr/scraper.py:57`, `ebay/scraper.py:90`

**Tasks**:
- [ ] Replace all `except:` with specific exception types
- [ ] Add proper error logging
- [ ] Ensure KeyboardInterrupt and SystemExit not caught
- [ ] Add linting rule to prevent future bare excepts

**Implementation**:
```python
# BEFORE:
try:
    await page.wait_for_selector('[class*="lot"]', timeout=10000)
except:  # ❌
    pass

# AFTER:
try:
    await page.wait_for_selector('[class*="lot"]', timeout=10000)
except TimeoutError:
    logger.warning(f"Selector not found after 10s timeout for URL: {url}")
    return None
except Exception as e:
    logger.error(f"Unexpected error waiting for selector: {e}", exc_info=True)
    raise
```

**Linting Rule** (add to `pyproject.toml` or `ruff.toml`):
```toml
[tool.ruff.lint]
select = ["E722"]  # Bare except
```

---

### C5: Standardize ORM Model Syntax
**Impact**: Type safety inconsistency, harder maintenance
**Effort**: 3 hours
**Files**: `backend/src/infrastructure/persistence/orm.py`

**Tasks**:
- [ ] Convert `orm.py` from legacy `Column()` to modern `Mapped[T]` + `mapped_column()`
- [ ] Ensure type hints match across all models
- [ ] Run mypy to verify type safety
- [ ] Update CLAUDE.md with ORM patterns

**Example Conversion**:
```python
# BEFORE (Legacy):
class CoinModel(Base):
    __tablename__ = "coins_v2"

    id = Column(Integer, primary_key=True)
    category = Column(String, nullable=False)
    metal = Column(String, nullable=False)
    weight_g = Column(Numeric(10, 3), nullable=True)

# AFTER (Modern):
class CoinModel(Base):
    __tablename__ = "coins_v2"

    id: Mapped[int] = mapped_column(primary_key=True)
    category: Mapped[str] = mapped_column(String)
    metal: Mapped[str] = mapped_column(String)
    weight_g: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 3))
```

---

## Priority 2: HIGH (Missing Critical Features)

### H1: Restore Import/Export Router (1,025 lines)
**Impact**: Users cannot add coins via URL import (primary workflow)
**Effort**: 5 days
**Files**: Create `backend/src/infrastructure/web/routers/import_v2.py`

**Dependencies**: Requires refactoring V1 services into Clean Architecture

**Tasks**:
- [ ] **Day 1**: Create domain services
  - Extract `DuplicateDetector` logic → `src/domain/services/duplicate_detection.py`
  - Extract `AuctionOrchestrator` → `src/domain/services/scraper_orchestrator.py` (extend existing)
  - Extract `NGCConnector` → `src/infrastructure/external/ngc_client.py`
- [ ] **Day 2**: Create use cases
  - `ImportFromURLUseCase` → `src/application/commands/import_from_url.py`
  - `ImportFromNGCUseCase` → `src/application/commands/import_from_ngc.py`
  - `BatchImportUseCase` → `src/application/commands/batch_import.py`
- [ ] **Day 3**: Create router endpoints
  - `POST /api/v2/import/from-url` - Parse auction URL, preview coin data
  - `POST /api/v2/import/from-ngc` - Lookup NGC certificate
  - `POST /api/v2/import/check-duplicate` - Check for existing coin
- [ ] **Day 4**: Additional endpoints
  - `POST /api/v2/import/confirm` - Create coin from previewed data
  - `POST /api/v2/import/batch-urls` - Process multiple URLs
  - `POST /api/v2/import/collection` - Excel/CSV upload (use existing `ExcelImporter`)
- [ ] **Day 5**: Testing & integration
  - Unit tests for use cases (mock repositories)
  - Integration tests for full import workflow
  - Frontend integration testing

**V1 Reference**: `backend/v1_archive/app/routers/import_export.py`

**Estimated Total**: 40 hours

---

### H2: Restore Catalog Integration Router (535 lines)
**Impact**: No catalog enrichment = core feature missing
**Effort**: 4 days
**Files**: Create `backend/src/infrastructure/web/routers/catalog_v2.py`

**Dependencies**: Requires database models for `ReferenceType` and `CoinReference`

**Tasks**:
- [ ] **Day 1**: Restore missing database models
  - Add `ReferenceTypeModel` to `orm.py`
  - Add `CoinReferenceModel` to `orm.py`
  - Create migration script or run `init_db()`
- [ ] **Day 2**: Refactor catalog services
  - Extract OCRE client → `src/infrastructure/external/ocre_client.py`
  - Extract RPC client → `src/infrastructure/external/rpc_client.py`
  - Extract CRRO client → `src/infrastructure/external/crro_client.py`
  - Create `ICatalogService` protocol in domain
- [ ] **Day 3**: Create use cases
  - `LookupReferenceUseCase` → `src/application/commands/lookup_reference.py`
  - `EnrichFromCatalogUseCase` → `src/application/commands/enrich_from_catalog.py`
  - `BulkEnrichUseCase` → `src/application/commands/bulk_enrich.py` (with job queue)
- [ ] **Day 4**: Create router & testing
  - `POST /api/v2/catalog/lookup` - Query external catalogs
  - `POST /api/v2/catalog/enrich/{coin_id}` - Enrich single coin
  - `POST /api/v2/catalog/bulk-enrich` - Background job
  - `GET /api/v2/catalog/job/{job_id}` - Job status polling
  - Unit + integration tests

**V1 Reference**: `backend/v1_archive/app/routers/catalog.py`

**Estimated Total**: 32 hours

---

### H3: Fix Image Upload in CreateCoin Endpoint
**Impact**: Cannot create coins with images in one request
**Effort**: 4 hours
**Files**: `backend/src/application/commands/create_coin.py`, `backend/src/infrastructure/web/routers/v2.py`

**Tasks**:
- [ ] Add `images: List[ImageDTO]` to `CreateCoinDTO`
- [ ] Update `CreateCoinUseCase` to handle images
- [ ] Remove TODO comment at `v2.py:158`
- [ ] Add test for coin creation with images

**Implementation**:
```python
# create_coin.py
@dataclass
class ImageDTO:
    url: str
    image_type: str
    is_primary: bool = False

@dataclass
class CreateCoinDTO:
    # ... existing fields ...
    images: List[ImageDTO] = field(default_factory=list)

class CreateCoinUseCase:
    def execute(self, dto: CreateCoinDTO) -> Coin:
        # ... existing logic ...

        # Add images to coin
        for img_dto in dto.images:
            coin.add_image(img_dto.url, img_dto.image_type, img_dto.is_primary)

        # Save coin
        return self.repository.save(coin)
```

```python
# v2.py:140-163
@router.post("", response_model=CoinResponse)
def create_coin(request: CreateCoinRequest, repo: ICoinRepository = Depends(get_coin_repo)):
    dto = CreateCoinDTO(
        # ... existing fields ...
        images=[ImageDTO(url=img.url, image_type=img.image_type, is_primary=img.is_primary)
                for img in request.images]  # ✅ Pass images
    )
    # ... rest of method
```

---

### H4: Restore Auction Management Router (198 lines)
**Impact**: No auction data CRUD, price comparables, market analysis
**Effort**: 2 days
**Files**: Create `backend/src/infrastructure/web/routers/auctions_v2.py`

**Tasks**:
- [ ] **Day 1**: Create repository & use cases
  - Implement `SqlAlchemyAuctionDataRepository` fully (currently minimal)
  - Create `ListAuctionsUseCase`
  - Create `GetComparablesUseCase`
  - Create `LinkAuctionToCoinUseCase`
- [ ] **Day 2**: Create router endpoints & testing
  - `GET /api/v2/auctions` - List with filters (house, date range, issuer)
  - `GET /api/v2/auctions/{id}` - Get single auction lot
  - `GET /api/v2/auctions/comparables/{reference_type_id}` - Price analysis
  - `POST /api/v2/auctions/{id}/link/{coin_id}` - Link to coin
  - `GET /api/v2/auctions/houses` - List distinct auction houses
  - Tests for all endpoints

**V1 Reference**: `backend/v1_archive/app/routers/auctions.py`

**Estimated Total**: 16 hours

---

### H5: Fix Audit Router (Replace Mock Data)
**Impact**: Audit feature is non-functional (uses hardcoded test data)
**Effort**: 2 days
**Files**: `backend/src/infrastructure/web/routers/audit_v2.py:40-49`

**Tasks**:
- [ ] Remove hardcoded mock `ExternalAuctionData`
- [ ] Fetch real auction data from `AuctionDataRepository`
- [ ] Integrate trust matrix from `domain/audit/trust.py`
- [ ] Add strategy configuration (weight tolerances per source)
- [ ] Add discrepancy severity levels
- [ ] Add tests with real auction data fixtures

**Implementation**:
```python
# audit_v2.py - BEFORE:
external_data = []
if coin.attribution.issuer.lower() == "augustus" or coin.acquisition is None:
    external_data.append(ExternalAuctionData(...))  # ❌ MOCK

# AFTER:
auction_repo = SqlAlchemyAuctionDataRepository(db)
auction_lot = auction_repo.get_by_coin_id(coin_id)

if not auction_lot:
    raise HTTPException(404, "No auction data found for this coin")

external_data = [ExternalAuctionData(
    source=auction_lot.source,
    lot_number=auction_lot.lot_id,
    grade=auction_lot.grade,
    issuer=auction_lot.issuer,
    weight_g=auction_lot.weight,
    # ... map all fields
)]
```

---

### H6: Add Comprehensive Unit Tests (0% → 70% coverage)
**Impact**: High risk of regressions, difficult refactoring
**Effort**: 2 weeks
**Files**: Create `backend/tests/` directory structure

**Tasks**:
- [ ] **Week 1**: Domain & Application layer tests
  - Day 1-2: Domain entity tests (`test_coin.py`, `test_auction.py`, `test_series.py`)
  - Day 3-4: Value object tests (`test_dimensions.py`, `test_attribution.py`)
  - Day 5: Strategy tests (`test_audit_strategies.py`)
  - Day 6-7: Use case tests (mock repositories, test business logic)
- [ ] **Week 2**: Infrastructure & Integration tests
  - Day 8-9: Repository integration tests (real DB transactions)
  - Day 10-11: Router integration tests (FastAPI TestClient)
  - Day 12-13: Scraper tests (mock Playwright responses)
  - Day 14: End-to-end workflow tests (import, enrich, audit)

**Test Structure**:
```
backend/tests/
├── conftest.py                    # Fixtures: test DB, repos, clients
├── unit/
│   ├── domain/
│   │   ├── test_coin.py          # Coin aggregate, add_image, etc.
│   │   ├── test_auction.py       # AuctionLot entity
│   │   ├── test_series.py        # Series completion logic
│   │   ├── test_vocab.py         # Issuer, Mint entities
│   │   └── test_value_objects.py # Dimensions, Attribution, etc.
│   ├── application/
│   │   ├── test_create_coin.py   # CreateCoinUseCase
│   │   ├── test_enrich_coin.py   # EnrichCoinUseCase
│   │   ├── test_scrape_lot.py    # ScrapeAuctionLotUseCase
│   │   └── test_import.py        # Import use cases
│   └── infrastructure/
│       ├── services/
│       │   ├── test_vocab_normalizer.py
│       │   └── test_series_service.py
│       └── web/
│           └── routers/
│               ├── test_v2_router.py
│               └── test_series_router.py
├── integration/
│   ├── persistence/
│   │   ├── test_coin_repository.py      # DB operations
│   │   └── test_auction_repository.py
│   └── workflows/
│       ├── test_import_workflow.py      # End-to-end import
│       └── test_catalog_workflow.py     # End-to-end enrichment
└── fixtures/
    ├── coins.json                       # Sample coin data
    ├── auction_lots.json                # Sample auction data
    └── scraper_responses/               # Mock HTML/JSON responses
```

**Minimum Coverage Targets**:
- Domain entities: **90%**
- Use cases: **80%**
- Repositories: **70%**
- Routers: **60%**
- Overall: **70%**

**Estimated Total**: 80 hours (2 weeks)

---

## Priority 3: MEDIUM (Complete Feature Parity)

### M1: Restore Campaign Router (297 lines)
**Impact**: No automated Heritage enrichment
**Effort**: 2 days
**Files**: Create `backend/src/infrastructure/web/routers/campaign_v2.py`

**Tasks**:
- [ ] Refactor `EnrichmentCampaign` service into use case
- [ ] Create endpoints: `GET /status`, `POST /start`, `POST /process-one`
- [ ] Add background job queue integration (consider using Celery or FastAPI BackgroundTasks)
- [ ] Add tests

**V1 Reference**: `backend/v1_archive/app/routers/campaign.py`

**Estimated Total**: 16 hours

---

### M2: Restore Statistics Router (347 lines)
**Impact**: No collection analytics
**Effort**: 2 days
**Files**: Create `backend/src/infrastructure/web/routers/stats_v2.py`

**Tasks**:
- [ ] Create `GetCollectionStatsUseCase`
- [ ] Implement aggregation queries (count by category, metal, ruler, etc.)
- [ ] Add price statistics (total value, average, min/max)
- [ ] Add weight statistics by metal
- [ ] Create endpoints: `GET /api/v2/stats/summary`, `GET /api/v2/stats/breakdown`
- [ ] Add tests

**V1 Reference**: `backend/v1_archive/app/routers/stats.py`

**Estimated Total**: 16 hours

---

### M3: Restore Settings Router (256 lines)
**Impact**: No backup/restore, trust configuration
**Effort**: 1.5 days
**Files**: Create `backend/src/infrastructure/web/routers/settings_v2.py`

**Tasks**:
- [ ] Backup endpoint (`GET /api/v2/settings/backup`) - download SQLite file
- [ ] Restore endpoint (`POST /api/v2/settings/restore`) - upload and replace DB
- [ ] Trust matrix configuration endpoints
- [ ] Database info endpoint (size, record counts, schema version)
- [ ] Add backup to `backend/backups/` with timestamp before restore
- [ ] Add tests

**V1 Reference**: `backend/v1_archive/app/routers/settings.py`

**Estimated Total**: 12 hours

---

### M4: Add Coin Navigation Endpoint
**Impact**: Users can't navigate prev/next in filtered lists
**Effort**: 4 hours
**Files**: `backend/src/infrastructure/web/routers/v2.py`

**Tasks**:
- [ ] Add `GET /api/v2/coins/{coin_id}/navigation?filters=...` endpoint
- [ ] Return `{prev_id: int | null, next_id: int | null}`
- [ ] Apply same filters as list view
- [ ] Add tests

**Implementation**:
```python
@router.get("/{coin_id}/navigation")
def get_coin_navigation(
    coin_id: int,
    category: Optional[str] = None,
    metal: Optional[str] = None,
    # ... other filters
    repo: ICoinRepository = Depends(get_coin_repo)
):
    # Get filtered list of coin IDs
    all_coins = repo.get_all(filters=...)
    coin_ids = [c.id for c in all_coins]

    try:
        current_idx = coin_ids.index(coin_id)
        prev_id = coin_ids[current_idx - 1] if current_idx > 0 else None
        next_id = coin_ids[current_idx + 1] if current_idx < len(coin_ids) - 1 else None

        return {"prev_id": prev_id, "next_id": next_id}
    except ValueError:
        raise HTTPException(404, "Coin not found in filtered results")
```

---

### M5: Restore Missing Database Models
**Impact**: Cannot persist references, provenance, price history
**Effort**: 2 days
**Files**: `backend/src/infrastructure/persistence/orm.py`, `models_reference.py`, `models_provenance.py`

**Tasks**:
- [ ] **Day 1**: Add models
  - `ReferenceTypeModel` (catalog reference types: RIC I 207, etc.)
  - `CoinReferenceModel` (links coins to reference types)
  - `ProvenanceEventModel` (auction history per coin)
  - `PriceHistoryModel` (price tracking over time)
  - `ImportRecordModel` (import metadata, source tracking)
- [ ] **Day 2**: Create repositories & migrations
  - Implement repositories for each model
  - Create Alembic migration or manual SQL script
  - Update domain entities if needed
  - Add tests

**Models to Add**:
```python
# models_reference.py
class ReferenceTypeModel(Base):
    __tablename__ = "reference_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference_system: Mapped[str] = mapped_column(String(20))  # RIC, RPC, Crawford
    reference_number: Mapped[str] = mapped_column(String(50))   # "I 207"
    full_reference: Mapped[str] = mapped_column(String(100))    # "RIC I 207"
    external_uri: Mapped[Optional[str]] = mapped_column(String(200))
    cached_data: Mapped[Optional[str]] = mapped_column(Text)    # JSON from OCRE/RPC
    last_lookup: Mapped[Optional[datetime]]

    # Relationships
    coin_references: Mapped[List["CoinReferenceModel"]] = relationship(back_populates="reference_type")

class CoinReferenceModel(Base):
    __tablename__ = "coin_references"

    id: Mapped[int] = mapped_column(primary_key=True)
    coin_id: Mapped[int] = mapped_column(ForeignKey("coins_v2.id", ondelete="CASCADE"))
    reference_type_id: Mapped[int] = mapped_column(ForeignKey("reference_types.id"))
    confidence: Mapped[Optional[str]] = mapped_column(String(20))  # exact, probable, uncertain
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    coin: Mapped["CoinModel"] = relationship(back_populates="references")
    reference_type: Mapped["ReferenceTypeModel"] = relationship(back_populates="coin_references")

# models_provenance.py
class ProvenanceEventModel(Base):
    __tablename__ = "provenance_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    coin_id: Mapped[int] = mapped_column(ForeignKey("coins_v2.id", ondelete="CASCADE"))
    event_type: Mapped[str] = mapped_column(String(20))  # auction, dealer, private
    event_date: Mapped[Optional[date]]
    auction_house: Mapped[Optional[str]] = mapped_column(String(100))
    lot_number: Mapped[Optional[str]] = mapped_column(String(50))
    hammer_price: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    currency: Mapped[Optional[str]] = mapped_column(String(3))
    url: Mapped[Optional[str]] = mapped_column(String(500))
    notes: Mapped[Optional[str]] = mapped_column(Text)

    coin: Mapped["CoinModel"] = relationship(back_populates="provenance")
```

**Estimated Total**: 16 hours

---

### M6: Implement Specification Pattern for Queries
**Impact**: Better query abstraction, reduced coupling
**Effort**: 1.5 days
**Files**: `backend/src/domain/repositories.py`, `backend/src/infrastructure/repositories/coin_repository.py`

**Tasks**:
- [ ] Create `CoinSpecification` class with builder pattern
- [ ] Create `CoinSortField` enum
- [ ] Update `ICoinRepository.find()` to accept specification
- [ ] Refactor router to use specifications instead of raw strings
- [ ] Add tests

**Implementation**:
```python
# domain/repositories.py
from enum import Enum
from dataclasses import dataclass
from typing import Optional

class SortDirection(Enum):
    ASC = "asc"
    DESC = "desc"

class CoinSortField(Enum):
    CREATED = "created"
    YEAR = "year"
    PRICE = "price"
    ISSUER = "issuer"
    WEIGHT = "weight"

@dataclass
class CoinSpecification:
    """Specification pattern for coin queries."""

    category: Optional[Category] = None
    metal: Optional[Metal] = None
    issuer: Optional[str] = None
    year_start_min: Optional[int] = None
    year_start_max: Optional[int] = None
    grading_state: Optional[GradingState] = None

    skip: int = 0
    limit: int = 100
    order_by: Optional[CoinSortField] = None
    order_direction: SortDirection = SortDirection.ASC

class ICoinRepository(Protocol):
    def find(self, specification: CoinSpecification) -> List[Coin]:
        """Find coins matching specification."""
        ...

    def count(self, specification: Optional[CoinSpecification] = None) -> int:
        """Count coins matching specification."""
        ...
```

**Router Usage**:
```python
# v2.py - BEFORE:
@router.get("")
def list_coins(
    category: Optional[str] = None,
    metal: Optional[str] = None,
    sort_by: str = "created",  # ❌ String-based
    sort_dir: str = "asc",
    ...
):
    coins = repo.get_all(sort_by=sort_by, sort_dir=sort_dir, ...)

# AFTER:
@router.get("")
def list_coins(
    category: Optional[Category] = None,
    metal: Optional[Metal] = None,
    sort_by: CoinSortField = CoinSortField.CREATED,  # ✅ Type-safe
    sort_dir: SortDirection = SortDirection.ASC,
    ...
):
    spec = CoinSpecification(
        category=category,
        metal=metal,
        order_by=sort_by,
        order_direction=sort_dir,
        skip=skip,
        limit=limit
    )
    coins = repo.find(spec)
```

**Estimated Total**: 12 hours

---

## Priority 4: LOW (Code Quality & Tech Debt)

### L1: Remove Code Duplication
**Impact**: Maintenance burden, inconsistent updates
**Effort**: 1 day
**Files**: Multiple

**Tasks**:
- [ ] Refactor `legend_service.py` (10,901 lines identical copy from V1)
  - Extract domain knowledge into data files or database tables
  - Create proper service interface
  - Remove V1 copy after migration complete
- [ ] Refactor `search_service.py` (11,403 lines identical copy)
  - Similar refactoring approach
- [ ] Remove unused `_to_model()` method in `coin_repository.py:156-182`
- [ ] Consolidate scraper base classes (reduce duplication)

**Estimated Total**: 8 hours

---

### L2: Implement Unit of Work Pattern
**Impact**: Better transaction control, consistency
**Effort**: 1 day
**Files**: Create `backend/src/infrastructure/persistence/unit_of_work.py`

**Tasks**:
- [ ] Create `IUnitOfWork` protocol
- [ ] Implement `SqlAlchemyUnitOfWork`
- [ ] Update use cases to accept `IUnitOfWork` instead of individual repositories
- [ ] Add tests

**Implementation**:
```python
# unit_of_work.py
from typing import Protocol
from sqlalchemy.orm import Session

class IUnitOfWork(Protocol):
    @property
    def coins(self) -> ICoinRepository:
        ...

    @property
    def auction_data(self) -> IAuctionDataRepository:
        ...

    @property
    def series(self) -> ISeriesRepository:
        ...

    def commit(self) -> None:
        ...

    def rollback(self) -> None:
        ...

    def __enter__(self):
        ...

    def __exit__(self, exc_type, exc_val, exc_tb):
        ...

class SqlAlchemyUnitOfWork:
    def __init__(self, session: Session):
        self.session = session
        self._coins = SqlAlchemyCoinRepository(session)
        self._auction_data = SqlAlchemyAuctionDataRepository(session)
        self._series = SqlAlchemySeriesRepository(session)

    @property
    def coins(self) -> ICoinRepository:
        return self._coins

    @property
    def auction_data(self) -> IAuctionDataRepository:
        return self._auction_data

    @property
    def series(self) -> ISeriesRepository:
        return self._series

    def commit(self):
        self.session.commit()

    def rollback(self):
        self.session.rollback()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.rollback()
        self.session.close()
```

**Use Case Update**:
```python
# enrich_coin.py - BEFORE:
class EnrichCoinUseCase:
    def __init__(self, coin_repo: ICoinRepository, auction_repo: IAuctionDataRepository):
        self.coin_repo = coin_repo
        self.auction_repo = auction_repo

    def execute(self, dto: EnrichCoinDTO) -> Coin:
        coin = self.coin_repo.get_by_id(dto.coin_id)
        auction_lot = # ... scrape ...
        self.auction_repo.upsert(auction_lot, dto.coin_id)
        # Problem: No transaction boundary!

# AFTER:
class EnrichCoinUseCase:
    def __init__(self, uow: IUnitOfWork):
        self.uow = uow

    def execute(self, dto: EnrichCoinDTO) -> Coin:
        with self.uow:
            coin = self.uow.coins.get_by_id(dto.coin_id)
            auction_lot = # ... scrape ...
            self.uow.auction_data.upsert(auction_lot, dto.coin_id)
            self.uow.commit()  # ✅ Explicit transaction boundary
        return coin
```

**Estimated Total**: 8 hours

---

### L3: Add Domain Events
**Impact**: Enable extensibility, decouple features
**Effort**: 2 days
**Files**: Create `backend/src/domain/events.py`, event handlers

**Tasks**:
- [ ] Create domain event base class
- [ ] Define events: `CoinCreated`, `CoinEnriched`, `AuditCompleted`, `SeriesCompleted`
- [ ] Implement event dispatcher/mediator
- [ ] Add event handlers (e.g., recalculate series completion on coin added)
- [ ] Add tests

**Estimated Total**: 16 hours

---

### L4: Standardize Async/Sync Patterns
**Impact**: Consistency, future-proofing
**Effort**: 2 days
**Files**: All use cases and repositories

**Tasks**:
- [ ] Make all use cases async
- [ ] Make all repositories async
- [ ] Update routers to use async handlers
- [ ] Update tests

**Estimated Total**: 16 hours

---

### L5: Add Money Value Object
**Impact**: Better money handling, validation
**Effort**: 4 hours
**Files**: `backend/src/domain/coin.py`

**Tasks**:
- [ ] Create `Money` value object with `amount` + `Currency` enum
- [ ] Replace `price: Decimal + currency: str` pairs
- [ ] Add validation (no negative amounts, valid currencies)
- [ ] Add tests

**Estimated Total**: 4 hours

---

### L6: Implement Alembic Migrations
**Impact**: Professional schema versioning, safer migrations
**Effort**: 1.5 days
**Files**: Create `backend/alembic/` directory

**Tasks**:
- [ ] Initialize Alembic in backend
- [ ] Create initial migration from current schema
- [ ] Convert ad-hoc migration scripts to Alembic migrations
- [ ] Add pre-migration backup hook
- [ ] Update documentation in CLAUDE.md

**Estimated Total**: 12 hours

---

## Backlog Summary

| Priority | Count | Estimated Total Effort |
|----------|-------|------------------------|
| **P0: Blockers** | 6 items | **5 hours** |
| **P1: Critical** | 6 items | **145 hours** (3.5 weeks) |
| **P2: High** | 6 items | **180 hours** (4.5 weeks) |
| **P3: Medium** | 6 items | **84 hours** (2 weeks) |
| **P4: Low** | 6 items | **64 hours** (1.5 weeks) |
| **TOTAL** | **30 items** | **478 hours** (~12 weeks) |

---

## Quick Wins (Can Complete Today)

1. **B3**: Add `additional_images` field (15 min)
2. **B4**: Fix `add_image()` logic (30 min)
3. **B5**: Fix repository field mapping (5 min)
4. **C4**: Replace bare except clauses (1 hour)

**Total Quick Wins**: **~2 hours** to fix 4 critical bugs

---

## Next Steps

1. **Complete P0 items** (5 hours) - Make database functional
2. **Review and approve this backlog** with user
3. **Begin P1 items** - Focus on missing tables, indexes, N+1 queries
4. **Create Sprint 1 plan** from P1+P2 items for feature parity
