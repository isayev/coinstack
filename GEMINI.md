# CoinStack Project Context & Rules

## 1. Project Identity
**CoinStack** is a personal ancient coin collection management system (Roman, Greek, Byzantine).
- **Stack:** Python 3.12+ (FastAPI, SQLAlchemy 2.0), React 18 (Vite, TS, TanStack Query, Zustand, Tailwind).
- **Paths:** `backend/app`, `frontend/src`.

## 2. Critical Rules (Strict Enforcement)

### 🔴 Ports
- **Backend:** `8000` (Strict). Do not use 8001+.
- **Frontend:** `3000` (Strict). Proxy `/api` → `http://localhost:8000`.
- **Action:** If ports are busy, kill the process. Do not increment ports.

### 🔴 Git Authorship
- **Author:** `isayev <olexandr@olexandrisayev.com>`
- **Constraint:** ALL commits must be authored by this user.
- **Prohibited:** NO `Co-authored-by` trailers. NO mention of AI assistance in commit messages.

### 🔴 Database Safety
- **File:** `backend/coinstack_v2.db` (SQLite).
- **Rule:** timestamped backup to `backend/backups/` REQUIRED before any schema change/migration.
- **Retention:** Keep rolling 5 backups.

### 🔴 Scrapers
- **Standard:** Use "Rich" scrapers (`heritage_rich`, `cng`, `biddr`, `ebay_rich`) in `backend/app/services/scrapers/`.
- **Avoid:** Simple/legacy scrapers if a rich version exists.

### 🔴 Documentation
- **Sync Protocol:** Consult `design/` and `docs/ai-guide/` BEFORE changes.
- **Update:** Update documentation (`05-DATA-MODEL.md`, `07-API-REFERENCE.md`, etc.) AFTER any functional change.

## 3. Architecture Cheat Sheet
- **Models:** `backend/src/infrastructure/persistence/orm.py` (SQLAlchemy).
- **Domain:** `backend/src/domain/coin.py` (Entities).
- **API:** `backend/src/infrastructure/web/routers/` (Endpoints).
- **UI:** `frontend/src/features/` (CoinDetail, etc.), `frontend/src/components/`.
- **Schema:** `frontend/src/domain/schemas.ts` (Zod/TS).

## 4. Server Management
**Restart Protocol:**
1. Kill ALL processes on 8000 & 3000.
2. Start Backend: `python run_server.py`
3. Start Frontend: `npm run dev -- --port 3000`

## 5. Research Grade Features (V2.1)
- **Die Studies:** `obverse_die_id`, `reverse_die_id` (String).
- **Issue Status:** `official`, `fourree`, `imitation`, `barbarous`, `modern_fake` (Enum).
- **Metrology:** `specific_gravity` (Decimal).
- **Monograms:** `monograms` (Table), `coin_monograms` (Link).
- **Find Data:** `find_spot`, `find_date`.