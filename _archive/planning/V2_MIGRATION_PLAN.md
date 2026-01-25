# CoinStack V1 → V2 Migration Plan

**Version**: 1.0
**Date**: 2026-01-25
**Status**: V2 at 15% completion
**Goal**: Complete Clean Architecture migration with 100% feature parity

---

## Executive Summary

**Current State**:
- V2 has basic coin CRUD, minimal scraping, mock audit, new series/vocab features
- Missing: Import, catalog enrichment, auction management, campaign, stats, settings
- Database: Missing tables, no FKs, no indexes, N+1 queries everywhere
- Test coverage: 0%

**Target State**:
- All V1 features migrated to Clean Architecture
- Comprehensive test coverage (70%+)
- Production-ready database with indexes, FKs, proper migrations
- Frontend fully functional with V2 backend

**Timeline**: 12 weeks (3 months) with 1 developer @ 40 hrs/week

---

## Migration Strategy

### Approach: Incremental Migration with Parallel Operation

We'll keep V1 operational while migrating features to V2, using a **Feature Toggle Pattern**:

```
┌────────────────────────────────────────┐
│         Frontend (React)               │
└────────────────┬───────────────────────┘
                 │
         ┌───────▼────────┐
         │  API Gateway   │  ← Feature flags control routing
         │  (Nginx/FastAPI)│
         └───┬────────┬───┘
             │        │
      ┌──────▼──┐  ┌─▼──────┐
      │ V1 API  │  │ V2 API │
      │ (Keep)  │  │(Migrate)│
      └─────────┘  └────────┘
```

**Benefits**:
- No downtime - V1 handles traffic while V2 is built
- Gradual rollout - migrate features one at a time
- Easy rollback - toggle back to V1 if issues arise
- Validate each feature before moving to next

---

## Phase 0: Foundation (Week 1) - Emergency Fixes

**Goal**: Make V2 database functional and fix critical bugs

### Day 1: Database Infrastructure

**Morning (4 hours): Create Missing Tables & Enable FKs**
```bash
# 1. Backup current database
cd backend
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item "coinstack_v2.db" "backups/coinstack_v2_$timestamp.db"

# 2. Create missing tables
python -c "from src.infrastructure.persistence.database import init_db; init_db()"

# 3. Verify tables exist
sqlite3 coinstack_v2.db ".tables"
# Should show: coin_images_v2, auction_data_v2

# 4. Enable foreign key enforcement
```

**Tasks**:
- [x] Backup database to `backups/`
- [ ] Run `init_db()` to create `coin_images_v2` and `auction_data_v2`
- [ ] Add FK pragma to `database.py` (see REFACTORING_BACKLOG.md B2)
- [ ] Test FK enforcement with dummy data
- [ ] Document changes in CLAUDE.md

**Afternoon (4 hours): Critical Index Creation**
```bash
# Run index creation script
python src/infrastructure/scripts/add_indexes.py
```

**Tasks**:
- [ ] Create `add_indexes.py` script (from backlog C1)
- [ ] Add indexes: issuer, category, metal, year_start, acquisition_date
- [ ] Verify query plan uses indexes: `EXPLAIN QUERY PLAN SELECT ...`
- [ ] Measure query performance before/after
- [ ] Commit script to repo

**Deliverable**: Functional database with proper schema

---

### Day 2: Critical Bug Fixes

**Morning (4 hours): Domain Model Fixes**

**Tasks**:
- [ ] Add `additional_images` field to `AuctionLot` (15 min)
- [ ] Fix `Coin.add_image()` primary image logic (30 min)
- [ ] Add unit tests for both fixes (2 hours)
- [ ] Run all scrapers to verify fix (1 hour)

**Afternoon (4 hours): Repository Fixes**

**Tasks**:
- [ ] Fix field mapping bug in `coin_repository.py:172` (5 min)
- [ ] Remove `session.commit()` from `delete()` method (15 min)
- [ ] Add transaction management to router layer (2 hours)
- [ ] Add rollback handling in exception cases (1 hour)
- [ ] Integration tests for transaction management (1 hour)

**Deliverable**: No runtime crashes, proper transaction management

---

### Day 3: Code Quality Fixes

**Morning (4 hours): Replace Bare Except Clauses**

**Tasks**:
- [ ] Fix `agora/parser.py:86, 168`
- [ ] Fix `cng/scraper.py:55`
- [ ] Fix `biddr/scraper.py:57`
- [ ] Fix `ebay/scraper.py:90`
- [ ] Add linting rule to prevent future bare excepts
- [ ] Run linter: `ruff check src/`

**Afternoon (4 hours): N+1 Query Fixes**

**Tasks**:
- [ ] Add eager loading to `CoinRepository.get_by_id()` and `get_all()`
- [ ] Add eager loading to series list endpoint
- [ ] Write query profiling tests
- [ ] Measure performance improvement
- [ ] Document eager loading patterns in CLAUDE.md

**Deliverable**: Clean code, optimized queries

---

### Day 4: Repository Interfaces

**Morning (4 hours): Create Missing Interfaces**

**Tasks**:
- [ ] Add `IAuctionDataRepository` protocol to `domain/repositories.py`
- [ ] Add `ISeriesRepository` protocol
- [ ] Add `IVocabRepository` protocol
- [ ] Update type hints in all use cases
- [ ] Update dependency injection in `dependencies.py`

**Afternoon (4 hours): Update Use Cases**

**Tasks**:
- [ ] Fix `EnrichCoinUseCase` to use `IAuctionDataRepository` interface
- [ ] Update all use cases to depend on interfaces
- [ ] Verify no concrete infrastructure imports in application layer
- [ ] Run type checking: `mypy src/`

**Deliverable**: Proper dependency inversion, testable use cases

---

### Day 5: ORM Standardization & Testing

**Morning (4 hours): Modernize ORM Syntax**

**Tasks**:
- [ ] Convert `orm.py` from `Column()` to `Mapped[T]` + `mapped_column()`
- [ ] Ensure consistency with vocab/series models
- [ ] Run mypy to verify type safety
- [ ] Test all CRUD operations still work

**Afternoon (4 hours): Phase 0 Testing & Documentation**

**Tasks**:
- [ ] Write integration tests for database fixes
- [ ] Test scraper operations end-to-end
- [ ] Update CLAUDE.md with all changes
- [ ] Create Phase 0 retrospective notes
- [ ] Tag commit: `git tag v2-phase0-complete`

**Deliverable**: Stable V2 foundation ready for feature migration

---

## Phase 1: Restore Critical Features (Weeks 2-5)

**Goal**: Restore import workflow and catalog enrichment (V1's most-used features)

---

### Week 2: Import System (Part 1) - Domain & Application Layers

**Monday: Domain Services**

**Morning**: Duplicate Detection Service
```python
# Create: src/domain/services/duplicate_detection.py

class DuplicateDetector:
    """Pure domain logic for detecting duplicate coins."""

    def find_potential_duplicates(
        self,
        candidate: Coin,
        existing_coins: List[Coin]
    ) -> List[DuplicateMatch]:
        """Compare candidate against existing coins."""
        matches = []

        for existing in existing_coins:
            score = self._calculate_similarity(candidate, existing)
            if score > 0.8:  # Threshold for "likely duplicate"
                matches.append(DuplicateMatch(
                    coin_id=existing.id,
                    similarity_score=score,
                    matching_fields=self._get_matching_fields(candidate, existing)
                ))

        return matches

    def _calculate_similarity(self, coin1: Coin, coin2: Coin) -> float:
        # Compare: issuer, year, denomination, weight, diameter
        # Return 0.0 to 1.0 similarity score
        ...
```

**Tasks**:
- [ ] Extract duplicate detection logic from V1 `services/duplicate_detector.py`
- [ ] Refactor into pure domain service (no DB, no infrastructure)
- [ ] Add unit tests with fixture coins
- [ ] Document algorithm in docstrings

**Afternoon**: Scraper Orchestrator Enhancement
- [ ] Extend existing `ScraperOrchestrator` with error handling
- [ ] Add retry logic with exponential backoff
- [ ] Add rate limiting per scraper
- [ ] Add logging for scraper operations
- [ ] Unit tests with mocked scrapers

---

**Tuesday: Application Layer - Import Use Cases (Part 1)**

**Morning**: `ImportFromURLUseCase`
```python
# Create: src/application/commands/import_from_url.py

@dataclass
class ImportFromURLDTO:
    url: str
    check_duplicates: bool = True

@dataclass
class ImportPreviewResult:
    coin_data: Coin  # Scraped coin data
    auction_data: Optional[AuctionLot]
    potential_duplicates: List[DuplicateMatch]
    warnings: List[str]

class ImportFromURLUseCase:
    def __init__(
        self,
        scraper_orchestrator: ScraperOrchestrator,
        coin_repo: ICoinRepository,
        duplicate_detector: DuplicateDetector
    ):
        self.scraper_orchestrator = scraper_orchestrator
        self.coin_repo = coin_repo
        self.duplicate_detector = duplicate_detector

    async def execute(self, dto: ImportFromURLDTO) -> ImportPreviewResult:
        # 1. Scrape URL
        auction_lot = await self.scraper_orchestrator.scrape(dto.url)
        if not auction_lot:
            raise ValueError(f"Unable to scrape URL: {dto.url}")

        # 2. Convert auction lot to coin domain model
        coin = self._map_auction_to_coin(auction_lot)

        # 3. Check for duplicates
        duplicates = []
        if dto.check_duplicates:
            existing_coins = self.coin_repo.get_all()
            duplicates = self.duplicate_detector.find_potential_duplicates(
                coin, existing_coins
            )

        # 4. Generate warnings
        warnings = self._generate_warnings(coin, auction_lot)

        return ImportPreviewResult(
            coin_data=coin,
            auction_data=auction_lot,
            potential_duplicates=duplicates,
            warnings=warnings
        )
```

**Tasks**:
- [ ] Create `ImportFromURLUseCase` with preview logic
- [ ] Map `AuctionLot` → `Coin` domain entity
- [ ] Integrate duplicate detection
- [ ] Generate validation warnings
- [ ] Unit tests with mocked dependencies

**Afternoon**: `ConfirmImportUseCase`
- [ ] Create use case to save previewed coin
- [ ] Accept user modifications to scraped data
- [ ] Persist coin + auction data in transaction
- [ ] Unit tests

---

**Wednesday: Application Layer - Import Use Cases (Part 2)**

**Morning**: `ImportFromNGCUseCase`

**Tasks**:
- [ ] Create NGC client in `infrastructure/external/ngc_client.py`
- [ ] Extract NGC scraping logic from V1
- [ ] Create use case to lookup NGC certificate
- [ ] Return coin data + images from NGC PhotoVision
- [ ] Unit tests with mocked NGC responses

**Afternoon**: `BatchImportUseCase`

**Tasks**:
- [ ] Create use case for batch URL processing
- [ ] Use async concurrency for parallel scraping
- [ ] Aggregate results (success, failed, duplicates)
- [ ] Add progress tracking mechanism
- [ ] Unit tests

---

**Thursday: Infrastructure Layer - NGC Client**

**Morning**: NGC Web Scraping
```python
# Create: src/infrastructure/external/ngc_client.py

class NGCClient:
    """Client for NGC certification lookup."""

    BASE_URL = "https://www.ngccoin.com/certlookup/"

    def __init__(self, http_client: IHttpClient):
        self.http_client = http_client

    async def lookup_certificate(self, cert_number: str) -> Optional[NGCCoinData]:
        """Look up NGC certificate and extract coin data."""
        url = f"{self.BASE_URL}{cert_number}/"

        html = await self.http_client.get(url)
        if not html:
            return None

        # Parse HTML for coin data
        soup = BeautifulSoup(html, 'html.parser')

        return NGCCoinData(
            cert_number=cert_number,
            grade=self._parse_grade(soup),
            issuer=self._parse_issuer(soup),
            denomination=self._parse_denomination(soup),
            year=self._parse_year(soup),
            images=self._parse_images(soup),  # PhotoVision images
            # ... more fields
        )
```

**Tasks**:
- [ ] Implement NGC HTML parsing
- [ ] Handle PhotoVision image URLs
- [ ] Add error handling for invalid certs
- [ ] Cache NGC lookups (avoid re-scraping)
- [ ] Integration tests with real NGC data (use fixtures)

**Afternoon**: HTTP Client Abstraction
- [ ] Create `IHttpClient` protocol
- [ ] Implement `HttpxClient` adapter
- [ ] Use in NGC client and vocab sync
- [ ] Unit tests with mocked HTTP

---

**Friday: Testing & Integration**

**Morning**: Integration Testing
- [ ] Test full import-from-URL workflow
- [ ] Test NGC import workflow
- [ ] Test batch import
- [ ] Test duplicate detection with real data
- [ ] Verify transaction rollback on errors

**Afternoon**: Code Review & Cleanup
- [ ] Review all new code for architecture violations
- [ ] Remove any temporary hacks
- [ ] Update CLAUDE.md with import patterns
- [ ] Create pull request for Week 2 work
- [ ] Tag: `git tag v2-import-domain-complete`

---

### Week 3: Import System (Part 2) - API & Frontend Integration

**Monday: Import Router (Part 1)**

**Morning**: URL Import Endpoint
```python
# Create: src/infrastructure/web/routers/import_v2.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, HttpUrl

router = APIRouter(prefix="/api/v2/import", tags=["import"])

class ImportURLRequest(BaseModel):
    url: HttpUrl
    check_duplicates: bool = True

class ImportURLResponse(BaseModel):
    coin: CoinPreview
    auction_data: Optional[AuctionLotPreview]
    potential_duplicates: List[DuplicateMatchResponse]
    warnings: List[str]

@router.post("/from-url", response_model=ImportURLResponse)
async def import_from_url(
    request: ImportURLRequest,
    use_case: ImportFromURLUseCase = Depends(get_import_url_use_case)
):
    """
    Preview coin data from auction URL.
    Returns scraped data, potential duplicates, warnings.
    User must confirm to create coin.
    """
    try:
        dto = ImportFromURLDTO(url=str(request.url), check_duplicates=request.check_duplicates)
        result = await use_case.execute(dto)

        return ImportURLResponse(
            coin=CoinPreview.from_domain(result.coin_data),
            auction_data=AuctionLotPreview.from_domain(result.auction_data) if result.auction_data else None,
            potential_duplicates=[
                DuplicateMatchResponse.from_domain(dup) for dup in result.potential_duplicates
            ],
            warnings=result.warnings
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Scraping failed: {e}")
```

**Tasks**:
- [ ] Create `import_v2.py` router
- [ ] Add `POST /from-url` endpoint
- [ ] Create Pydantic response models
- [ ] Add dependency injection for use cases
- [ ] OpenAPI docs/examples

**Afternoon**: Confirm Import Endpoint
- [ ] Add `POST /confirm` endpoint
- [ ] Accept user-modified coin data
- [ ] Call `ConfirmImportUseCase`
- [ ] Return created coin with ID
- [ ] Add tests

---

**Tuesday: Import Router (Part 2)**

**Morning**: NGC & Batch Endpoints
- [ ] Add `POST /from-ngc` endpoint
- [ ] Add `POST /batch-urls` endpoint with BackgroundTasks
- [ ] Add `GET /batch-status/{job_id}` for progress tracking
- [ ] Tests for all endpoints

**Afternoon**: Excel Import Endpoint
- [ ] Add `POST /collection` (file upload)
- [ ] Reuse existing `ExcelImporter` from infrastructure
- [ ] Return import summary (success/failed counts)
- [ ] Tests with sample Excel files

---

**Wednesday: Frontend Integration (Import)**

**Morning**: API Client Updates
```typescript
// frontend/src/api/import.ts

export interface ImportURLRequest {
  url: string;
  check_duplicates: boolean;
}

export interface ImportURLResponse {
  coin: CoinPreview;
  auction_data?: AuctionLotPreview;
  potential_duplicates: DuplicateMatch[];
  warnings: string[];
}

export const importAPI = {
  fromURL: async (request: ImportURLRequest): Promise<ImportURLResponse> => {
    const response = await axios.post('/api/v2/import/from-url', request);
    return response.data;
  },

  confirm: async (coinData: CoinCreate): Promise<Coin> => {
    const response = await axios.post('/api/v2/import/confirm', coinData);
    return response.data;
  },

  fromNGC: async (certNumber: string): Promise<ImportURLResponse> => {
    const response = await axios.post('/api/v2/import/from-ngc', { cert_number: certNumber });
    return response.data;
  },
};
```

**Tasks**:
- [ ] Add import API client functions
- [ ] Create TypeScript types matching V2 response schemas
- [ ] Add TanStack Query hooks (`useImportFromURL`, etc.)

**Afternoon**: Import Page UI
- [ ] Update import page to use V2 endpoints
- [ ] Add URL input form
- [ ] Add NGC certificate lookup form
- [ ] Display preview with duplicate warnings
- [ ] Add "Confirm Import" button

---

**Thursday: Excel Import & Duplicate Resolution UI**

**Morning**: Excel Upload Component
- [ ] Add file upload dropzone
- [ ] Show upload progress
- [ ] Display import summary
- [ ] Handle errors gracefully

**Afternoon**: Duplicate Resolution UI
- [ ] Create duplicate comparison component
- [ ] Show side-by-side comparison of candidate vs existing coin
- [ ] Allow user to skip, replace, or import as new
- [ ] Add tests

---

**Friday: Testing & Documentation**

**Morning**: End-to-End Testing
- [ ] Test complete import workflow (URL → preview → confirm)
- [ ] Test NGC import workflow
- [ ] Test Excel import
- [ ] Test duplicate detection UX
- [ ] Test error scenarios

**Afternoon**: Documentation & Release
- [ ] Update CLAUDE.md with import workflows
- [ ] Create migration notes for users
- [ ] Tag release: `git tag v2-import-complete`
- [ ] Deploy to staging for user testing

---

### Week 4: Catalog Integration (Part 1) - Database & Domain

**Monday: Database Models for References**

**Morning**: Create Reference Models
```python
# Add to src/infrastructure/persistence/orm.py or create models_reference.py

class ReferenceTypeModel(Base):
    """Catalog reference types (RIC I 207, RPC IV.3 1234, etc.)"""
    __tablename__ = "reference_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    reference_system: Mapped[str] = mapped_column(String(20), index=True)  # RIC, RPC, Crawford
    volume: Mapped[Optional[str]] = mapped_column(String(20))  # "I", "IV.3"
    number: Mapped[str] = mapped_column(String(50))  # "207", "1234a"
    full_reference: Mapped[str] = mapped_column(String(100), unique=True, index=True)  # "RIC I 207"

    # External catalog data
    external_uri: Mapped[Optional[str]] = mapped_column(String(500))  # OCRE/RPC URL
    cached_data: Mapped[Optional[str]] = mapped_column(Text)  # JSON from catalog
    last_lookup: Mapped[Optional[datetime]]

    # Relationships
    coin_references: Mapped[List["CoinReferenceModel"]] = relationship(
        back_populates="reference_type", cascade="all, delete-orphan"
    )

class CoinReferenceModel(Base):
    """Junction table: Coins ↔ References (many-to-many)"""
    __tablename__ = "coin_references"

    id: Mapped[int] = mapped_column(primary_key=True)
    coin_id: Mapped[int] = mapped_column(ForeignKey("coins_v2.id", ondelete="CASCADE"), index=True)
    reference_type_id: Mapped[int] = mapped_column(ForeignKey("reference_types.id"), index=True)

    # Confidence level
    confidence: Mapped[str] = mapped_column(String(20), default="exact")  # exact, probable, uncertain
    notes: Mapped[Optional[str]] = mapped_column(Text)

    # Relationships
    coin: Mapped["CoinModel"] = relationship(back_populates="references")
    reference_type: Mapped["ReferenceTypeModel"] = relationship(back_populates="coin_references")

    __table_args__ = (
        UniqueConstraint('coin_id', 'reference_type_id', name='uq_coin_reference'),
    )
```

**Tasks**:
- [ ] Create `ReferenceTypeModel` and `CoinReferenceModel`
- [ ] Add relationship to `CoinModel`: `references: Mapped[List[CoinReferenceModel]]`
- [ ] Create migration script or run `init_db()`
- [ ] Add indexes on foreign keys
- [ ] Verify schema with `sqlite3 coinstack_v2.db ".schema reference_types"`

**Afternoon**: Reference Domain Entities
```python
# Add to src/domain/coin.py or create src/domain/reference.py

@dataclass(frozen=True)
class CatalogReference:
    """Value object representing a catalog reference."""
    system: str  # "RIC", "RPC", "Crawford"
    volume: Optional[str]  # "I", "IV.3"
    number: str  # "207", "1234a"
    confidence: str = "exact"  # exact, probable, uncertain
    notes: Optional[str] = None

    @property
    def full_reference(self) -> str:
        """Format as 'RIC I 207' or 'RPC IV.3 1234a'"""
        if self.volume:
            return f"{self.system} {self.volume} {self.number}"
        return f"{self.system} {self.number}"

# Update Coin entity
@dataclass
class Coin:
    # ... existing fields ...
    references: List[CatalogReference] = field(default_factory=list)

    def add_reference(self, reference: CatalogReference):
        """Add catalog reference if not duplicate."""
        if reference not in self.references:
            self.references.append(reference)

    def get_primary_reference(self) -> Optional[CatalogReference]:
        """Get highest-confidence reference."""
        if not self.references:
            return None
        # Return first "exact" reference, or first reference
        exact = [r for r in self.references if r.confidence == "exact"]
        return exact[0] if exact else self.references[0]
```

**Tasks**:
- [ ] Create `CatalogReference` value object
- [ ] Add `references` field to `Coin` aggregate
- [ ] Add methods: `add_reference()`, `get_primary_reference()`
- [ ] Unit tests

---

**Tuesday: External Catalog Clients**

**Morning**: OCRE Client (Online Coins of the Roman Empire)
```python
# Create: src/infrastructure/external/ocre_client.py

class OCREClient:
    """Client for OCRE (RIC) catalog lookups."""

    BASE_URL = "http://numismatics.org/ocre/"
    SPARQL_ENDPOINT = "http://numismatics.org/ocre/sparql"

    async def lookup_ric(self, volume: str, number: str) -> Optional[OCRECoinData]:
        """
        Look up RIC reference in OCRE.

        Args:
            volume: "I", "II", "III", etc.
            number: "207", "58b", etc.

        Returns:
            Coin metadata from OCRE or None if not found
        """
        # OCRE uses RDF/SPARQL queries
        query = f"""
        PREFIX nm: <http://nomisma.org/id/>
        PREFIX nmo: <http://nomisma.org/ontology#>
        PREFIX dcterms: <http://purl.org/dc/terms/>

        SELECT ?coinType ?issuer ?denomination ?obverse ?reverse ?weight ?diameter
        WHERE {{
            ?coinType a nmo:TypeSeriesItem ;
                dcterms:source <http://numismatics.org/ocre/id/ric.{volume}.{number}> ;
                nmo:hasAuthority ?issuer ;
                nmo:hasDenomination ?denomination ;
                nmo:hasObverse ?obv ;
                nmo:hasReverse ?rev .

            OPTIONAL {{ ?coinType nmo:hasWeight ?weight }}
            OPTIONAL {{ ?coinType nmo:hasDiameter ?diameter }}

            ?obv nmo:hasLegend ?obverse .
            ?rev nmo:hasLegend ?reverse .
        }}
        """

        response = await self.http_client.post(
            self.SPARQL_ENDPOINT,
            data={"query": query, "format": "json"}
        )

        if not response or "results" not in response:
            return None

        # Parse SPARQL JSON results
        return self._parse_sparql_results(response["results"]["bindings"])
```

**Tasks**:
- [ ] Implement OCRE SPARQL client
- [ ] Parse RDF/JSON results
- [ ] Extract: issuer, denomination, legends, weight, diameter
- [ ] Handle missing/partial data gracefully
- [ ] Add caching (Redis or in-memory LRU)
- [ ] Unit tests with mocked SPARQL responses

**Afternoon**: RPC Client (Roman Provincial Coinage)
- [ ] Implement similar SPARQL client for RPC
- [ ] RPC endpoint: `http://numismatics.org/rpc/`
- [ ] Parse RPC-specific data structure
- [ ] Tests

---

**Wednesday: Catalog Service & Use Cases**

**Morning**: Catalog Service (Domain)
```python
# Create: src/domain/services/catalog_service.py

class CatalogService:
    """Domain service for catalog operations."""

    def __init__(
        self,
        ocre_client: OCREClient,
        rpc_client: RPCClient,
        crro_client: CRROClient
    ):
        self.clients = {
            "RIC": ocre_client,
            "RPC": rpc_client,
            "Crawford": crro_client,
        }

    async def lookup_reference(self, reference: CatalogReference) -> Optional[CatalogData]:
        """Look up reference in appropriate external catalog."""
        client = self.clients.get(reference.system)
        if not client:
            return None

        if reference.system == "RIC":
            return await client.lookup_ric(reference.volume, reference.number)
        elif reference.system == "RPC":
            return await client.lookup_rpc(reference.volume, reference.number)
        elif reference.system == "Crawford":
            return await client.lookup_crawford(reference.number)

        return None

    def compare_coin_to_catalog(
        self,
        coin: Coin,
        catalog_data: CatalogData
    ) -> CatalogComparison:
        """Compare coin fields against catalog data."""
        discrepancies = []

        # Compare issuer
        if coin.attribution.issuer != catalog_data.issuer:
            discrepancies.append(FieldDiscrepancy(
                field="issuer",
                local_value=coin.attribution.issuer,
                catalog_value=catalog_data.issuer,
                severity="high"
            ))

        # Compare weight (with tolerance)
        if catalog_data.weight:
            weight_diff = abs(coin.dimensions.weight_g - catalog_data.weight)
            if weight_diff > 0.5:  # 0.5g tolerance
                discrepancies.append(FieldDiscrepancy(
                    field="weight",
                    local_value=str(coin.dimensions.weight_g),
                    catalog_value=str(catalog_data.weight),
                    severity="medium"
                ))

        # Compare other fields...

        return CatalogComparison(
            reference=coin.get_primary_reference(),
            discrepancies=discrepancies,
            confidence_score=self._calculate_confidence(discrepancies)
        )
```

**Tasks**:
- [ ] Create `CatalogService` domain service
- [ ] Implement `lookup_reference()` method
- [ ] Implement `compare_coin_to_catalog()` method
- [ ] Calculate confidence scores
- [ ] Unit tests with mocked clients

**Afternoon**: Lookup Use Case
```python
# Create: src/application/commands/lookup_reference.py

@dataclass
class LookupReferenceDTO:
    reference: str  # "RIC I 207"

class LookupReferenceUseCase:
    def __init__(
        self,
        catalog_service: CatalogService,
        reference_repo: IReferenceRepository
    ):
        self.catalog_service = catalog_service
        self.reference_repo = reference_repo

    async def execute(self, dto: LookupReferenceDTO) -> CatalogLookupResult:
        # 1. Parse reference string
        parsed = self._parse_reference(dto.reference)
        if not parsed:
            raise ValueError(f"Invalid reference format: {dto.reference}")

        # 2. Check cache (database)
        cached = self.reference_repo.get_by_full_reference(dto.reference)
        if cached and not self._is_stale(cached):
            return CatalogLookupResult.from_cached(cached)

        # 3. Look up in external catalog
        catalog_data = await self.catalog_service.lookup_reference(parsed)
        if not catalog_data:
            return CatalogLookupResult(found=False, reference=dto.reference)

        # 4. Cache result
        reference_type = self.reference_repo.create_or_update(
            reference=parsed,
            catalog_data=catalog_data
        )

        return CatalogLookupResult.from_catalog(catalog_data, reference_type.id)
```

**Tasks**:
- [ ] Create `LookupReferenceUseCase`
- [ ] Parse reference strings (reuse V1 parser)
- [ ] Implement caching strategy
- [ ] Unit tests

---

**Thursday: Enrich Use Case & Repository**

**Morning**: Reference Repository
```python
# Create: src/infrastructure/repositories/reference_repository.py

class SqlAlchemyReferenceRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_full_reference(self, full_reference: str) -> Optional[ReferenceType]:
        """Get cached reference by full string (e.g., 'RIC I 207')"""
        model = self.session.query(ReferenceTypeModel).filter(
            ReferenceTypeModel.full_reference == full_reference
        ).first()

        return self._to_domain(model) if model else None

    def create_or_update(
        self,
        reference: CatalogReference,
        catalog_data: CatalogData
    ) -> ReferenceType:
        """Cache catalog lookup results."""
        model = self.session.query(ReferenceTypeModel).filter(
            ReferenceTypeModel.full_reference == reference.full_reference
        ).first()

        if model:
            # Update existing
            model.cached_data = json.dumps(catalog_data.to_dict())
            model.last_lookup = datetime.utcnow()
        else:
            # Create new
            model = ReferenceTypeModel(
                reference_system=reference.system,
                volume=reference.volume,
                number=reference.number,
                full_reference=reference.full_reference,
                cached_data=json.dumps(catalog_data.to_dict()),
                last_lookup=datetime.utcnow()
            )
            self.session.add(model)

        self.session.flush()
        return self._to_domain(model)

    def link_to_coin(self, coin_id: int, reference_type_id: int, confidence: str = "exact"):
        """Create coin ↔ reference link."""
        link = CoinReferenceModel(
            coin_id=coin_id,
            reference_type_id=reference_type_id,
            confidence=confidence
        )
        self.session.add(link)
        self.session.flush()
```

**Tasks**:
- [ ] Implement `SqlAlchemyReferenceRepository`
- [ ] Add caching methods
- [ ] Add coin linking methods
- [ ] Integration tests

**Afternoon**: Enrich Coin Use Case
```python
# Create: src/application/commands/enrich_from_catalog.py

@dataclass
class EnrichFromCatalogDTO:
    coin_id: int
    reference: str  # "RIC I 207"
    auto_apply: bool = False  # Auto-apply high-confidence matches

class EnrichFromCatalogUseCase:
    async def execute(self, dto: EnrichFromCatalogDTO) -> EnrichmentResult:
        # 1. Get coin
        coin = self.coin_repo.get_by_id(dto.coin_id)
        if not coin:
            raise ValueError(f"Coin {dto.coin_id} not found")

        # 2. Look up catalog reference
        lookup_result = await self.lookup_use_case.execute(
            LookupReferenceDTO(reference=dto.reference)
        )
        if not lookup_result.found:
            raise ValueError(f"Reference not found: {dto.reference}")

        # 3. Compare coin to catalog
        comparison = self.catalog_service.compare_coin_to_catalog(
            coin, lookup_result.catalog_data
        )

        # 4. Auto-apply if requested and high confidence
        if dto.auto_apply and comparison.confidence_score > 0.9:
            coin = self._apply_catalog_data(coin, lookup_result.catalog_data)
            self.coin_repo.save(coin)

        # 5. Link reference to coin
        self.reference_repo.link_to_coin(
            dto.coin_id,
            lookup_result.reference_type_id,
            confidence="exact"
        )

        return EnrichmentResult(
            coin=coin,
            comparison=comparison,
            applied=dto.auto_apply
        )
```

**Tasks**:
- [ ] Create `EnrichFromCatalogUseCase`
- [ ] Implement comparison logic
- [ ] Implement auto-apply with confidence threshold
- [ ] Unit tests

---

**Friday: Testing & Integration**

**Morning**: Integration Tests
- [ ] Test OCRE lookup with real SPARQL endpoint
- [ ] Test RPC lookup
- [ ] Test full enrich workflow (lookup → compare → apply)
- [ ] Test caching behavior
- [ ] Test error scenarios (reference not found, network errors)

**Afternoon**: Week 4 Wrap-up
- [ ] Code review
- [ ] Update CLAUDE.md
- [ ] Tag: `git tag v2-catalog-domain-complete`

---

### Week 5: Catalog Integration (Part 2) - API & UI

**Monday-Wednesday**: Catalog Router & Frontend (similar to Week 3)
- Create `/api/v2/catalog` router
- Add endpoints: `/lookup`, `/enrich/{coin_id}`, `/bulk-enrich`
- Frontend integration
- UI for catalog comparison drawer

**Thursday-Friday**: Testing & Documentation
- End-to-end testing
- User acceptance testing
- Documentation
- Tag: `git tag v2-catalog-complete`

---

## Phase 2: Complete Feature Parity (Weeks 6-9)

### Week 6: Auction Management + Campaign
- Restore auction router
- Implement campaign automation
- Price comparables & market analysis

### Week 7: Statistics + Settings
- Collection statistics dashboard
- Backup/restore functionality
- Trust matrix configuration UI

### Week 8: Missing Database Models
- Restore provenance, price history, import records models
- Data migration from V1
- Historical data preservation

### Week 9: Buffer & Polish
- Fix discovered bugs
- Performance optimization
- UI polish
- Documentation

---

## Phase 3: Testing & Quality (Weeks 10-12)

### Week 10: Comprehensive Testing
- Achieve 70%+ test coverage
- End-to-end workflow tests
- Performance testing
- Security review

### Week 11: Production Hardening
- Error handling review
- Logging & monitoring setup
- Backup automation
- Deployment automation

### Week 12: Migration & Cutover
- V1 → V2 data migration script
- Parallel deployment
- Gradual traffic shift
- V1 deprecation

---

## Success Criteria

### Phase 0 (Week 1)
- ✅ Database has all tables, FKs enabled, indexes created
- ✅ Zero critical bugs (no runtime crashes)
- ✅ All scrapers functional
- ✅ Clean architecture violations fixed

### Phase 1 (Weeks 2-5)
- ✅ Import workflow fully functional (URL, NGC, Excel)
- ✅ Catalog enrichment working (OCRE, RPC lookups)
- ✅ Frontend can create coins via import
- ✅ Tests: 40%+ coverage for new features

### Phase 2 (Weeks 6-9)
- ✅ All V1 routers migrated to V2
- ✅ All V1 features working in V2
- ✅ No frontend breaking changes
- ✅ Tests: 60%+ coverage

### Phase 3 (Weeks 10-12)
- ✅ Production-ready: monitoring, backups, error handling
- ✅ Tests: 70%+ coverage
- ✅ V1 fully replaced by V2
- ✅ Documentation complete

---

## Risk Mitigation

### Risk 1: Timeline Overrun
**Mitigation**:
- Each phase has 20% buffer time
- Can skip non-critical features (campaign, advanced stats)
- Parallel V1/V2 operation allows gradual migration

### Risk 2: Breaking Changes
**Mitigation**:
- Feature flags control V2 activation
- Comprehensive testing before each release
- Easy rollback to V1 if issues arise

### Risk 3: Data Loss During Migration
**Mitigation**:
- Automated backups before each migration step (per GEMINI.md)
- Keep 5 rolling backups
- Test migration on copy of production DB first
- Maintain V1 database as backup during transition

### Risk 4: Performance Degradation
**Mitigation**:
- Performance testing in Phase 3
- Database indexes created in Phase 0
- N+1 query fixes in Phase 0
- Monitor query performance throughout

---

## Rollback Plan

If critical issues arise during migration:

1. **Immediate**: Toggle feature flag to route traffic back to V1
2. **Database**: Restore from most recent backup (kept in `backend/backups/`)
3. **Frontend**: Deploy previous frontend version that uses V1 API
4. **Investigate**: Review logs, fix issue, test in staging
5. **Retry**: Re-enable V2 after fix verified

**Rollback Time**: < 5 minutes (feature flag toggle)

---

## Monitoring & Metrics

Track throughout migration:

- **Test Coverage**: Target 70%, track weekly
- **API Response Times**: P50, P95, P99 latency
- **Error Rate**: < 1% for all endpoints
- **Feature Completeness**: % of V1 features in V2
- **Database Performance**: Query times, N+1 detection
- **User Feedback**: Bug reports, feature requests

---

## Next Steps

1. **Review this plan** with stakeholders
2. **Begin Phase 0** (Week 1) immediately
3. **Daily standups** to track progress
4. **Weekly retrospectives** to adjust plan
5. **Update this document** as we learn

---

**Last Updated**: 2026-01-25
**Plan Owner**: isayev
**Status**: Ready to Execute
