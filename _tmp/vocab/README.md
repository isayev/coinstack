# CoinStack 2026 Hardening Roadmap

## For AI Coding Assistants

This roadmap provides detailed technical specifications for hardening the CoinStack application. Each phase document is designed to be consumed by AI coding assistants with complete context and implementation guidance.

## Project Context

**CoinStack** is a single-user ancient Roman coin collection management system.

### Tech Stack
```
Backend:  Python 3.12+ / FastAPI / SQLAlchemy 2.0 / SQLite
Frontend: React 18 / TypeScript 5.x / Vite / TanStack Query / Zustand / Tailwind / shadcn/ui
```

### Directory Structure
```
coinstack/
├── backend/
│   └── app/
│       ├── main.py           # FastAPI application entry
│       ├── config.py         # Pydantic Settings configuration
│       ├── database.py       # SQLAlchemy engine/session
│       ├── models/           # SQLAlchemy ORM models
│       │   ├── coin.py       # Core Coin model
│       │   ├── vocab.py      # Controlled vocabulary (NEW)
│       │   └── series.py     # Collection series (NEW)
│       ├── schemas/          # Pydantic request/response schemas
│       ├── routers/          # FastAPI route handlers
│       ├── crud/             # Database operations
│       └── services/         # Business logic
│           ├── scrapers/     # Auction site scrapers
│           ├── catalogs/     # OCRE/CRRO/RPC integrations
│           ├── vocab_normalizer.py  # Vocabulary normalization (NEW)
│           ├── vocab_sync.py        # LOD sync service (NEW)
│           ├── series_service.py    # Series management (NEW)
│           └── audit/        # Audit and enrichment services
│
└── frontend/
    └── src/
        ├── App.tsx           # Root component
        ├── pages/            # Route page components
        ├── components/       # Reusable UI components
        │   ├── VocabAutocomplete.tsx  # Vocabulary selector (NEW)
        │   └── SeriesCard.tsx         # Series display (NEW)
        ├── hooks/            # TanStack Query hooks
        ├── stores/           # Zustand state stores
        ├── types/            # TypeScript type definitions
        └── lib/              # Utilities (api.ts, utils.ts)
```

---

## Roadmap Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        COINSTACK 2026 ROADMAP                               │
├─────────────────────────────────────────────────────────────────────────────┤
│ PHASE 1 (Week 1-2): CRITICAL DATA INTEGRITY                                 │
│   └─ Transactions, Locking, Constraints, Error Boundaries, Health Checks    │
├─────────────────────────────────────────────────────────────────────────────┤
│ PHASE 2 (Week 3-4): RELIABILITY & OBSERVABILITY                             │
│   └─ Circuit Breakers, Logging, Rate Limiting, Field Tracking, Testing      │
├─────────────────────────────────────────────────────────────────────────────┤
│ PHASE 2.5 (Week 5-6): CONTROLLED VOCABULARY  ⭐ NEW                          │
│   └─ Issuers, Mints, Denominations, LOD Sync, Alias Tables, Normalization   │
├─────────────────────────────────────────────────────────────────────────────┤
│ PHASE 2.7 (Week 7-8): COIN SERIES & COLLECTIONS  ⭐ NEW                      │
│   └─ Series Types, Slots, Templates, Completion Tracking, Gap Analysis      │
├─────────────────────────────────────────────────────────────────────────────┤
│ PHASE 3 (Week 9-10): OPERATIONAL IMPROVEMENTS                               │
│   └─ Idempotency, Scraper Versioning, Form Persistence, Backups, Metrics    │
├─────────────────────────────────────────────────────────────────────────────┤
│ PHASE 4 (Week 11+): POLISH & ENHANCEMENTS                                   │
│   └─ Response Envelopes, Offline Detection, Sanitization, Image Handling    │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Phase Documents

| Phase | Focus | Timeline | Effort | Document |
|-------|-------|----------|--------|----------|
| **Phase 1** | Critical Data Integrity | Week 1-2 | 5.5 days | [PHASE-1-CRITICAL.md](./PHASE-1-CRITICAL.md) |
| **Phase 2** | Reliability & Observability | Week 3-4 | 10 days | [PHASE-2-HIGH.md](./PHASE-2-HIGH.md) |
| **Phase 2.5** | Controlled Vocabulary ⭐ | Week 5-6 | 8 days | [VOCAB-IMPROVEMENTS-2026.md](./VOCAB-IMPROVEMENTS-2026.md) |
| **Phase 2.7** | Coin Series & Collections ⭐ | Week 7-8 | 10 days | [SERIES-FEATURE.md](./SERIES-FEATURE.md) |
| **Phase 3** | Operational Improvements | Week 9-10 | 7.5 days | [PHASE-3-MEDIUM.md](./PHASE-3-MEDIUM.md) |
| **Phase 4** | Polish & Enhancements | Week 11+ | 5 days | [PHASE-4-ENHANCEMENTS.md](./PHASE-4-ENHANCEMENTS.md) |

**Total Estimated Effort: ~46 days (10-11 weeks)**

---

## New Features Highlights

### ⭐ Controlled Vocabulary (Phase 2.5)

Standardizes terminology across the application with LOD integration:

| Component | Description |
|-----------|-------------|
| **Issuer Tables** | 238+ canonical rulers with temporal bounds, dynasty, aliases |
| **Mint Tables** | Geographic hierarchy, active periods, abbreviations |
| **Denomination Tables** | Metal types, weight standards, value relationships |
| **Alias System** | Legend forms → canonical (e.g., "IMP CAESAR DIVI F" → "Augustus") |
| **LOD Sync** | Weekly sync from Nomisma.org/OCRE/CRRO |
| **Normalization** | Multi-strategy matching: exact → alias → fuzzy → LLM |
| **Review Queue** | Human-in-the-loop for low-confidence matches |
| **Temporal Validation** | Warns if coin date doesn't match ruler's reign |

**Key Improvements Over Original Design:**
- 3-tier caching (Authority → Local Cache → Application)
- Offline capability with local SQLite vocabulary
- Calibrated confidence scoring by method
- VocabAssignment audit trail

### ⭐ Coin Series (Phase 2.7)

Comprehensive collection management:

| Component | Description |
|-----------|-------------|
| **7 Series Types** | Canonical, reference, dynastic, thematic, geographic, user, smart |
| **30+ Templates** | Twelve Caesars, Five Good Emperors, Legionary Denarii, etc. |
| **Slot System** | Defined positions with criteria, difficulty, rarity ratings |
| **Smart Series** | Auto-populated based on filter criteria |
| **Gap Analysis** | Missing items with acquisition difficulty assessment |
| **Wishlist Sync** | Series gaps → automatic wishlist items with alerts |
| **Completion Tracking** | Progress visualization, budget tracking per series |
| **Hierarchical Series** | Nested series (e.g., Imperial → Julio-Claudian → Augustus) |

**Canonical Series Templates Include:**
- The Twelve Caesars (Suetonius)
- Five Good Emperors
- Year of Four Emperors (69 AD)
- Severan Dynasty
- Legionary Denarii of Mark Antony
- Judaea Capta Series
- Travel Series of Hadrian
- Animals on Roman Coins

---

## Task ID Convention

Each task has a unique identifier:

| Pattern | Example | Meaning |
|---------|---------|---------|
| `P{n}-{nn}` | `P1-01` | Phase 1, Task 01 (Transaction Boundaries) |
| `PV-{nn}` | `PV-01` | Vocabulary Phase, Task 01 (Schema Setup) |
| `PS-{nn}` | `PS-01` | Series Phase, Task 01 (Core Tables) |

---

## Implementation Guidelines

### For AI Assistants

1. **Read the full task** before implementing
2. **Check prerequisites** - some tasks depend on others
3. **Follow the file modification order** listed in each task
4. **Include all code** - complete implementations, not snippets
5. **Add tests** as specified in acceptance criteria
6. **Use conventional commits**: `feat(P1-01): add transaction boundaries`

### Code Style

**Python (Backend)**
```python
# Type hints required
def get_coin(db: Session, coin_id: int) -> Coin | None:
    return db.query(Coin).filter(Coin.id == coin_id).first()

# Use structlog for logging
logger.info("coin_created", coin_id=coin.id, category=coin.category)

# Docstrings for public functions
def normalize_issuer(raw: str, context: dict | None = None) -> NormalizationResult:
    """
    Normalize a raw issuer string to canonical form.
    
    Args:
        raw: Raw input (e.g., "IMP NERVA CAES AVG")
        context: Optional context for better matching
        
    Returns:
        NormalizationResult with match details and confidence
    """
    ...
```

**TypeScript (Frontend)**
```typescript
// Explicit types for function parameters and returns
function useCoin(coinId: number): UseQueryResult<CoinDetail> {
  return useQuery({
    queryKey: ['coin', coinId],
    queryFn: () => fetchCoin(coinId),
  })
}

// Interface for component props
interface SeriesCardProps {
  series: SeriesListItem
  onSelect?: (id: number) => void
}
```

---

## Dependencies Graph

```
P1-01 Transaction Boundaries
  └─► P2-06 Test Infrastructure
  └─► P3-01 Request Idempotency

P2-02 Structured Logging
  └─► P2-04 Field Tracking
  └─► P3-05 Metrics Collection

P2-05 Reference Normalization
  └─► PV-* Controlled Vocabulary (all tasks)
       └─► PS-* Coin Series (all tasks)
            └─► PS-03 Gap Analysis
            └─► PS-04 Wishlist Integration

P2-01 Circuit Breaker
  └─► P3-02 Scraper Versioning
  └─► PV-02 LOD Sync Service (uses circuit breakers)
```

---

## Priority Summary

| Priority | Phase | Tasks | Effort |
|----------|-------|-------|--------|
| 🔴 Critical | 1 | P1-01 through P1-05 | 5.5 days |
| 🟠 High | 2 | P2-01 through P2-06 | 10 days |
| 🟣 Core Feature | 2.5 | Controlled Vocabulary | 8 days |
| 🟣 Core Feature | 2.7 | Coin Series | 10 days |
| 🟡 Medium | 3 | P3-01 through P3-06 | 7.5 days |
| 🟢 Enhancement | 4 | P4-01 through P4-05 | 5 days |

---

## Quick Reference

### Key Backend Files
- `backend/app/database.py` - Session management
- `backend/app/models/coin.py` - Core Coin model (72 fields)
- `backend/app/models/vocab.py` - Controlled vocabulary models ⭐
- `backend/app/models/series.py` - Series management models ⭐
- `backend/app/crud/coin.py` - Coin CRUD operations
- `backend/app/services/coin_service.py` - Business logic
- `backend/app/services/vocab_normalizer.py` - Vocabulary normalization ⭐
- `backend/app/services/vocab_sync.py` - LOD sync service ⭐
- `backend/app/services/series_service.py` - Series management ⭐

### Key Frontend Files  
- `frontend/src/lib/api.ts` - Axios instance configuration
- `frontend/src/hooks/useCoins.ts` - TanStack Query hooks
- `frontend/src/hooks/useSeries.ts` - Series query hooks ⭐
- `frontend/src/stores/filterStore.ts` - Zustand filter state
- `frontend/src/components/ErrorBoundary.tsx` - Error handling
- `frontend/src/components/VocabAutocomplete.tsx` - Vocabulary selector ⭐
- `frontend/src/pages/SeriesDashboard.tsx` - Series overview ⭐
- `frontend/src/pages/SeriesDetail.tsx` - Series slots view ⭐

### Running Tests
```bash
# Backend
cd backend
uv run pytest -v
uv run pytest --cov=app

# Frontend
cd frontend
npm test
npm run lint
```

### Database Migrations
```bash
cd backend

# Run all migrations
uv run alembic upgrade head

# Individual migration scripts
python -m migrations.add_version_column
python -m migrations.add_vocab_tables
python -m migrations.add_series_tables
```

### Vocabulary Sync Commands
```bash
cd backend

# Sync from Nomisma.org (issuers, mints, denominations)
uv run python -m app.scripts.sync_vocab

# Load canonical series templates
uv run python -m app.scripts.load_series_templates

# Normalize existing coins
uv run python -m app.scripts.normalize_existing_coins
```

---

## External API Dependencies

| API | Purpose | Rate Limit | Cache TTL |
|-----|---------|------------|-----------|
| Nomisma.org SPARQL | Issuers, Mints, Denominations | ~100/min | 1 week |
| OCRE Reconciliation | RIC type lookup | ~100/min | 1 year |
| CRRO Reconciliation | Crawford type lookup | ~100/min | 1 year |
| RPC (no API) | Provincial reference (manual) | N/A | Manual |

---

## Success Metrics

After completing all phases:

| Metric | Before | After |
|--------|--------|-------|
| Transaction Safety | ❌ | ✅ |
| Concurrent Edit Protection | ❌ | ✅ |
| Scraper Resilience | ⚠️ | ✅ |
| Observability | ⚠️ | ✅ |
| Test Coverage | ~0% | >70% |
| Data Provenance | ⚠️ | ✅ |
| Vocabulary Standardization | ❌ | ✅ |
| Series/Collection Tracking | ❌ | ✅ |
| Gap Analysis | ❌ | ✅ |
| Wishlist Management | ❌ | ✅ |
| Error Recovery | ⚠️ | ✅ |
| Backup Automation | ❌ | ✅ |
| Offline Capability | ❌ | ✅ |
