# CoinStack AI Developer Guide

> A comprehensive reference for AI coding assistants working on the CoinStack codebase.

## Quick Start - Load This Context First

When starting a development session, load these files for essential context:

```
1. This file (README.md) - Navigation and overview
2. 01-OVERVIEW.md - Domain knowledge and terminology
3. 02-ARCHITECTURE.md - System structure and diagrams
```

Then load the relevant module guide based on your task:
- Backend work → `03-BACKEND-MODULES.md`
- Frontend work → `04-FRONTEND-MODULES.md`
- Database changes → `05-DATA-MODEL.md`

## Document Index

| File | Purpose | When to Use |
|------|---------|-------------|
| [01-OVERVIEW.md](01-OVERVIEW.md) | Project context, domain terms, tech stack | Starting any task |
| [02-ARCHITECTURE.md](02-ARCHITECTURE.md) | System diagrams, layer organization | Understanding structure |
| [03-BACKEND-MODULES.md](03-BACKEND-MODULES.md) | Python modules, services, routers | Backend development |
| [04-FRONTEND-MODULES.md](04-FRONTEND-MODULES.md) | React components, hooks, stores | Frontend development |
| [05-DATA-MODEL.md](05-DATA-MODEL.md) | Database schema, relationships, enums | Data layer changes |
| [backend/SCHEMA.md](../../backend/SCHEMA.md) | **Full database schema** (72 coin columns) | Detailed DB reference |
| [06-DATA-FLOWS.md](06-DATA-FLOWS.md) | Request flows, state management | Understanding processes |
| [07-API-REFERENCE.md](07-API-REFERENCE.md) | API endpoints, request/response | API integration |
| [08-CODING-PATTERNS.md](08-CODING-PATTERNS.md) | Conventions, patterns, standards | Writing new code |
| [09-TASK-RECIPES.md](09-TASK-RECIPES.md) | Step-by-step guides for common tasks | Implementing features |

## Project at a Glance

**CoinStack** is a personal ancient coin collection management system for numismatists.

```
Tech Stack:
├── Backend:  Python 3.12+ / FastAPI / SQLAlchemy 2.0 / SQLite
├── Frontend: React 18 / TypeScript 5.x / Vite / TanStack Query / Zustand
└── UI:       Tailwind CSS / shadcn/ui
```

```
Project Structure:
coinstack/
├── backend/
│   └── app/
│       ├── main.py          # FastAPI entry point
│       ├── models/          # SQLAlchemy ORM models
│       ├── schemas/         # Pydantic schemas
│       ├── routers/         # API endpoints
│       ├── crud/            # Database operations
│       └── services/        # Business logic
├── frontend/
│   └── src/
│       ├── App.tsx          # React entry point
│       ├── pages/           # Route pages
│       ├── components/      # React components
│       ├── hooks/           # TanStack Query hooks
│       ├── stores/          # Zustand stores
│       └── types/           # TypeScript types
└── docs/
    └── ai-guide/            # This documentation
```

## Key Domain Concepts

| Term | Definition |
|------|------------|
| Coin | Central entity - an ancient coin in the collection |
| Obverse | Front of coin (usually portrait) |
| Reverse | Back of coin (design/legend) |
| Legend | Text inscribed on coin |
| Mint | Location where coin was struck |
| Reference | Catalog citation (RIC, RPC, Crawford) |
| Denomination | Coin type (Denarius, Aureus, Sestertius) |

## Common Tasks Quick Reference

| Task | Key Files |
|------|-----------|
| Add field to Coin | `models/coin.py` → `schemas/coin.py` → `crud/coin.py` |
| New API endpoint | `routers/*.py` → `services/*.py` → `crud/*.py` |
| New React page | `pages/*.tsx` → `App.tsx` (routes) → `hooks/*.ts` |
| New scraper | `services/scrapers/*.py` → `routers/scrape.py` |
| Modify filters | `stores/filterStore.ts` → `hooks/useCoins.ts` |

## Development Commands

```bash
# Backend
cd backend
uv run uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm run dev     # Start dev server on :3000
npm run build   # Production build
npm run lint    # ESLint check
```

## API Base URLs

- Frontend Dev: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

## External Resources

### Auction Sites (Scrapers)

| Site | URL |
|------|-----|
| Heritage Auctions | https://coins.ha.com |
| CNG | https://cngcoins.com |
| Biddr | https://biddr.com |
| Roma Numismatics | https://romanumismatics.com |
| Agora Auctions | https://agoraauctions.com |
| eBay | https://www.ebay.com |

### Reference Catalogs

| Catalog | URL |
|---------|-----|
| OCRE (RIC) | http://numismatics.org/ocre/ |
| CRRO (Crawford) | http://numismatics.org/crro/ |
| RPC Online | https://rpc.ashmus.ox.ac.uk/ |

### Grading Services

| Service | URL |
|---------|-----|
| NGC | https://www.ngccoin.com |
| PCGS | https://www.pcgs.com |

---

*Navigate to specific guides using the Document Index above.*
