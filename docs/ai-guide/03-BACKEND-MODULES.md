# Backend Modules Reference (V2 Clean Architecture)

## Directory Structure

```
backend/src/
├── domain/                    # Domain Layer (no dependencies)
│   ├── coin.py                # Coin entity + value objects + enums
│   ├── auction.py             # AuctionLot entity
│   ├── series.py              # Series entity
│   ├── vocab.py               # VocabTerm entity
│   ├── llm.py                 # LLM interfaces and result types
│   ├── repositories.py        # Repository interfaces (Protocols)
│   ├── services/              # Domain services
│   │   ├── audit_engine.py
│   │   ├── search_service.py
│   │   ├── scraper_orchestrator.py
│   │   └── scraper_service.py # Scraper protocol and result types
│   └── strategies/            # Audit strategies
│
├── application/               # Application Layer (use cases)
│   └── commands/
│       ├── create_coin.py
│       ├── enrich_coin.py
│       └── ...
│
└── infrastructure/            # Infrastructure Layer (external concerns)
    ├── persistence/           # Database & ORM
    │   ├── orm.py             # Core ORM models (SQLAlchemy)
    │   └── repositories/      # Concrete repository implementations
    │       ├── coin_repository.py
    │       └── ...
    │
    ├── mappers/               # Data Mappers (NEW)
    │   └── coin_mapper.py     # Domain <-> ORM mapping logic
    │
    ├── scrapers/              # Auction scrapers
    │   ├── base_playwright.py # Base class with anti-bot logic
    │   ├── heritage/
    │   ├── cng/
    │   └── ...
    │
    ├── services/              # Infrastructure services
    │   ├── llm_service.py     # LLM Facade
    │   ├── llm/               # Specialized LLM Services
    │   │   ├── base_client.py
    │   │   ├── identification.py
    │   │   ├── context.py
    │   │   ├── parsing.py
    │   │   └── normalization.py
    │   └── catalogs/          # Catalog Clients (OCRE, RPC)
    │
    └── web/                   # Web layer (FastAPI)
        └── routers/           # API endpoints
```

---

## Domain Layer (`src/domain/`)

### `coin.py` - Coin Entity

**Coin** is the aggregate root. It uses `slots=True` for memory optimization and `EnrichmentData` for LLM results.

```python
@dataclass(frozen=True, slots=True)
class EnrichmentData:
    """LLM-generated enrichment data."""
    historical_significance: str | None = None
    suggested_references: List[str] | None = None
    # ...

@dataclass
class Coin:
    # ... standard fields ...
    
    # Value Objects
    dimensions: Dimensions
    attribution: Attribution
    grading: GradingDetails
    
    # Enrichment
    enrichment: EnrichmentData | None = None
```

### `scraper_service.py` - Scraper Protocol

Defines the contract for all scrapers using `ScrapeResult` for robust error handling.

```python
class ScrapeStatus(str, Enum):
    SUCCESS = "success"
    NOT_FOUND = "not_found"
    BLOCKED = "blocked"
    ERROR = "error"

@dataclass
class ScrapeResult(Generic[T]):
    status: ScrapeStatus
    data: Optional[T] = None
    error_message: Optional[str] = None

class IScraper(Protocol):
    async def scrape(self, url: str) -> ScrapeResult[AuctionLot]:
        ...
```

---

## Infrastructure Layer (`src/infrastructure/`)

### Mappers (`src/infrastructure/mappers/`)

#### `coin_mapper.py`

Decouples persistence logic from object mapping. Handles complex transformations including JSON deserialization safety.

```python
class CoinMapper:
    @staticmethod
    def to_domain(model: CoinModel) -> Coin:
        # Maps ORM model to Coin entity
        # Handles safe JSON parsing for enrichment fields
        ...

    @staticmethod
    def to_model(coin: Coin) -> CoinModel:
        # Maps Coin entity to ORM model
        # Flattening value objects to columns
        ...
```

### Repositories (`src/infrastructure/repositories/`)

#### `coin_repository.py`

Now simplified to focus on database operations, delegating mapping to `CoinMapper`.

```python
class SqlAlchemyCoinRepository(ICoinRepository):
    def get_by_id(self, coin_id: int) -> Optional[Coin]:
        orm_coin = self.session.query(CoinModel).options(
            selectinload(CoinModel.images),
            # ...
        ).filter(CoinModel.id == coin_id).first()
        return CoinMapper.to_domain(orm_coin) if orm_coin else None

    def save(self, coin: Coin) -> Coin:
        orm_coin = CoinMapper.to_model(coin)
        merged = self.session.merge(orm_coin)
        self.session.flush()
        return CoinMapper.to_domain(merged)
```

### LLM Services (`src/infrastructure/services/llm/`)

Refactored from a "God Class" into a **Facade pattern** with specialized services.

*   **`llm_service.py`**: The Facade implementing `ILLMService`. Delegates requests.
*   **`base_client.py`**: Handles API calls (LiteLLM), Cost Tracking, Rate Limiting, and Caching.
*   **`identification.py`**: Vision capabilities (Identify, Transcribe).
*   **`context.py`**: RAG and Narrative generation.
*   **`normalization.py`**: Vocab and Legend cleaning.
*   **`parsing.py`**: Structure extraction from text.

### Scrapers (`src/infrastructure/scrapers/`)

#### `base_playwright.py`

Enhanced base class for robustness:
*   **Anti-Bot**: Automatic User-Agent rotation and stealth headers.
*   **Rate Limiting**: Per-domain delays with jitter.
*   **Retry Logic**: Exponential backoff for network errors.

---

## Key Patterns Update

### 1. Mapper Pattern
Use `CoinMapper` instead of private `_to_domain` methods in repositories to strictly separate concerns.

### 2. Facade Pattern
Use `LLMService` as a facade for the complex subsystem of LLM clients, caches, and processors.

### 3. Result Wrappers
Use `ScrapeResult` and `LLMResult` to encapsulate success/failure states along with metadata (confidence, cost, error details), rather than throwing exceptions for expected operational failures (like 404s).