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
│       ├── schemas/          # Pydantic request/response schemas
│       ├── routers/          # FastAPI route handlers
│       ├── crud/             # Database operations
│       └── services/         # Business logic
│           ├── scrapers/     # Auction site scrapers
│           ├── catalogs/     # OCRE/CRRO/RPC integrations
│           └── audit/        # Audit and enrichment services
│
└── frontend/
    └── src/
        ├── App.tsx           # Root component
        ├── pages/            # Route page components
        ├── components/       # Reusable UI components
        ├── hooks/            # TanStack Query hooks
        ├── stores/           # Zustand state stores
        ├── types/            # TypeScript type definitions
        └── lib/              # Utilities (api.ts, utils.ts)
```

## Phase Documents

| Phase | Focus | Timeline | Document |
|-------|-------|----------|----------|
| **Phase 1** | Critical Data Integrity | Week 1-2 | [PHASE-1-CRITICAL.md](./PHASE-1-CRITICAL.md) |
| **Phase 2** | High-Priority Reliability | Week 3-4 | [PHASE-2-HIGH.md](./PHASE-2-HIGH.md) |
| **Phase 3** | Medium-Priority Improvements | Week 5-6 | [PHASE-3-MEDIUM.md](./PHASE-3-MEDIUM.md) |
| **Phase 4** | Nice-to-Have Enhancements | Week 7+ | [PHASE-4-ENHANCEMENTS.md](./PHASE-4-ENHANCEMENTS.md) |

## Task ID Convention

Each task has a unique identifier: `P{phase}-{number}`

Examples:
- `P1-01` = Phase 1, Task 01 (Transaction Boundaries)
- `P2-03` = Phase 2, Task 03 (Rate Limiting)

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
    ...

# Docstrings for public functions
def create_coin(db: Session, coin_data: CoinCreate) -> Coin:
    """
    Create a new coin with all related entities.
    
    Args:
        db: Database session
        coin_data: Validated coin creation data
        
    Returns:
        Created Coin instance with relationships loaded
        
    Raises:
        IntegrityError: If constraints violated
    """
    ...
```

**TypeScript (Frontend)**
```typescript
// Explicit types for function parameters and returns
function useCoin(coinId: number): UseQueryResult<CoinDetail> {
  ...
}

// Interface for component props
interface CoinCardProps {
  coin: CoinListItem
  onClick?: () => void
}
```

## Priority Summary

| Priority | Count | Total Effort |
|----------|-------|--------------|
| P1 - Critical | 5 tasks | ~5.5 days |
| P2 - High | 6 tasks | ~10 days |
| P3 - Medium | 6 tasks | ~7.5 days |
| P4 - Enhancement | 5 tasks | ~6 days |

## Quick Reference

### Key Backend Files
- `backend/app/database.py` - Session management
- `backend/app/models/coin.py` - Core Coin model (72 fields)
- `backend/app/crud/coin.py` - Coin CRUD operations
- `backend/app/services/coin_service.py` - Business logic (create in P1-01)

### Key Frontend Files  
- `frontend/src/lib/api.ts` - Axios instance configuration
- `frontend/src/hooks/useCoins.ts` - TanStack Query hooks
- `frontend/src/stores/filterStore.ts` - Zustand filter state
- `frontend/src/components/ErrorBoundary.tsx` - Error handling (create in P1-04)

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
# Run migration script
cd backend
python -m migrations.{migration_name}

# Or with explicit path
python migrations/add_version_column.py
```
