# CoinStack Project Context & Rules

## 1. Project Identity
**CoinStack** is a personal ancient coin collection management system (Roman, Greek, Byzantine).
- **Stack:** 
  - **Backend:** Python 3.12+ (FastAPI, SQLAlchemy 2.0, Pydantic 2.x, SQLite).
  - **Frontend:** React 18 (Vite, TS, TanStack Query, Zustand, Tailwind, shadcn/ui).
- **Paths:** `backend/app`, `frontend/src`.

## 2. Domain Context
**CoinStack** manages ancient numismatic data. Key terms and structures:

### Domain Terms
- **Denomination**: Coin type (Denarius, Antoninianus, Solidus, etc.)
- **Metal**: Gold (AU), Silver (AR), Bronze (AE), Billon
- **Obverse**: Front of coin (usually portrait)
- **Reverse**: Back of coin (usually design/legend)
- **Legend**: Text inscribed on coin
- **Exergue**: Area below main reverse design
- **Die Axis**: Orientation between obverse and reverse (0-12h)
- **Reference**: Standard catalogs (RIC, RPC, RSC)
- **Slab**: Encapsulated graded coin (NGC, PCGS)

### Categories
- **Republic**: Roman Republic (509-27 BC)
- **Imperial**: Roman Empire (27 BC - 476 AD)
- **Provincial**: Roman provincial/Greek Imperial
- **Byzantine**: Byzantine Empire (330-1453 AD)
- **Greek**: Ancient Greek city-states

## 3. Critical Rules (Strict Enforcement)

### 🔴 Ports
- **Backend:** `8000` (Strict). Do not use 8001+.
- **Frontend:** `3000` (Strict). Proxy `/api` → `http://localhost:8000`.
- **Action:** If ports are busy, kill the process. Do not increment ports.
- **Config:** `frontend/vite.config.ts` must proxy to `http://localhost:8000`.

### 🔴 Git Authorship
- **Author:** `isayev <olexandr@olexandrisayev.com>`
- **Constraint:** ALL commits must be authored by this user.
- **Prohibited:** NO `Co-authored-by` trailers. NO mention of AI assistance in commit messages.

### 🔴 Database Safety
- **File:** `backend/coinstack_v2.db` (SQLite).
- **Rule:** timestamped backup to `backend/backups/` REQUIRED before any schema change/migration.
- **Retention:** Keep rolling 5 backups.
- **Commands:**
  ```powershell
  # Backup
  $timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
  Copy-Item "backend\coinstack_v2.db" "backend\backups\coinstack_$timestamp.db"
  ```

### 🔴 Documentation Sync Protocol (ZERO TOLERANCE)
**BEFORE any functionality change:**
1. CONSULT `design/` specs (for UI).
2. CONSULT `docs/ai-guide/` guides.
3. UNDERSTAND existing patterns.

**AFTER any functionality change:**
1. UPDATE `docs/ai-guide/` (API Ref, Data Model, Components, etc.).
2. VERIFY documentation matches implementation.

**Verification Checklist:**
- [ ] Consulted specs/guides BEFORE coding.
- [ ] Updated `docs/ai-guide/` AFTER coding.
- [ ] `05-DATA-MODEL.md` reflects DB changes.
- [ ] `07-API-REFERENCE.md` reflects API changes.
- [ ] `11-FRONTEND-COMPONENTS.md` reflects UI changes.

### 🔴 Scrapers
- **Standard:** Use "Rich" scrapers (`heritage_rich`, `cng`, `biddr`, `ebay_rich`) in `backend/src/infrastructure/scrapers/`.
- **Avoid:** Simple/legacy scrapers if a rich version exists.

## 4. Architecture & Organization

### Backend Structure (`backend/app/`)
- `models/`: SQLAlchemy models
- `schemas/`: Pydantic schemas
- `routers/`: FastAPI routers
- `services/`: Business logic
- `crud/`: Database operations

### Frontend Structure (`frontend/src/`)
- `features/`: Feature-based modules (CoinDetail, Dashboard)
- `components/`: Shared UI components
- `hooks/`: Custom hooks
- `stores/`: Zustand stores
- `domain/`: Zod schemas & types

## 5. Server Management
**Restart Protocol:**
1. Kill ALL processes on 8000 & 3000.
2. Start Backend: `cd backend && uv run run_server.py`
3. Start Frontend: `npm run dev -- --port 3000`

## 6. Research Grade Features (V2.1)
- **Die Studies:** `obverse_die_id`, `reverse_die_id` (String).
- **Issue Status:** `official`, `fourree`, `imitation`, `barbarous`, `modern_fake` (Enum).
- **Metrology:** `specific_gravity` (Decimal).
- **Monograms:** `monograms` (Table), `coin_monograms` (Link).
- **Find Data:** `find_spot`, `find_date`.

## Gemini Added Memories
- All commits and activity must be authored only by the user (isayev / olexandr@olexandrisayev.com). No AI assistant co-authorship or attribution should ever be included in commit messages or code.
- Pocket extraction optimization: 7.0A radius with ACE/NME capping and stiff minimization (K_BOND=600, W_STERIC=50) yields optimal correlation (R2=0.98) with full protein AIMNet2 scoring. Larger pockets (10A) diverge due to surface/error accumulation despite geometric fixes.
- The project has been upgraded to Research Grade V2.1, including die studies, issue status (fourree/imitation), specific gravity, and monograms. Documentation sync is now mandatory.
