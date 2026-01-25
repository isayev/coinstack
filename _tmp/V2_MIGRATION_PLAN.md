# CoinStack V2: Migration & Refactoring Plan

## Vision
Migrate the entire application to the new **Clean Architecture (V2)** core. The Backend is ready; the focus now shifts to the Frontend and remaining business features (Scraping/Enrichment).

## Core Principles
1.  **Frontend-Driven Validation**: The UI must reflect the new Domain structure (Aggregate Roots).
2.  **TDD Everywhere**: Frontend components and hooks must be tested before integration.
3.  **Strangler Fig Pattern**: We serve V2 API alongside V1 until the Frontend is fully migrated.

## Directory Structure (Target)
```
backend/
├── src/
│   ├── domain/              # Entities (Coin, Grading, etc.)
│   ├── application/         # Use Cases (CreateCoin, Import, Scrape)
│   ├── infrastructure/      # Adapters (FastAPI, SQLAlchemy, Scrapers)
frontend/
├── src/
│   ├── domain/              # TypeScript Types matching Backend Entities
│   ├── features/            # Feature-based folders (Coins, Import, Audit)
│   ├── api/                 # V2 API Client
└── tests/                   # Vitest tests
```

## Phased Implementation Roadmap

### Phase 1: Frontend Foundation & Migration
**Goal**: Point the React Application to the V2 API.

*   [ ] **P1-01**: **Frontend Test Setup**: Configure Vitest & React Testing Library.
*   [ ] **P1-02**: **Domain Types**: Create TS interfaces matching V2 Entities (`Coin`, `GradingDetails`).
*   [ ] **P1-03**: **API Client V2**: Create typed Axios client for `/api/v2`.
*   [ ] **P1-04**: **Coin List & Detail**: Refactor components to use V2 data structure (nested objects).
*   [ ] **P1-05**: **Create/Edit Forms**: Update forms to send V2 DTOs.

### Phase 2: Advanced Features (Porting to V2)
**Goal**: Re-implement Scraping and Enrichment using Clean Architecture.

*   [ ] **P2-01**: **Scraper Domain**: Define `IScraper` Port and `AuctionLot` Entity.
*   [ ] **P2-02**: **Scraper Adapters**: Port Heritage/CNG scrapers to `infrastructure/scrapers`.
*   [ ] **P2-03**: **Enrichment Use Case**: Implement `EnrichCoinUseCase` (Logic to update Coin from Scraper).
*   [ ] **P2-04**: **Audit UI**: Build Frontend UI for the new Audit Engine (Display Discrepancies).

### Phase 3: Reliability & Cleanup
**Goal**: Hardening and removing Legacy V1 code.

*   [ ] **P3-01**: **Circuit Breakers**: Implement resilience for external scrapers.
*   [ ] **P3-02**: **Rate Limiting**: Protect V2 endpoints.
*   [ ] **P3-03**: **Legacy Removal**: Drop V1 tables and delete `backend/app` (Legacy).

## TDD Strategy

### Backend (Already Established)
*   **Unit**: Pytest (Domain Logic).
*   **Integration**: Pytest + SQLite In-Memory (Repositories/API).

### Frontend (New)
*   **Unit**: Vitest (Functions/Utilities).
*   **Component**: Testing Library (Render components, fire events).
*   **Integration**: MSW (Mock Service Worker) to mock API responses.

## Metrics for Success
*   **Frontend**: 100% of read/write operations go to `/api/v2`.
*   **Tests**: Frontend Critical Path coverage > 80%.
*   **Legacy**: 0 lines of V1 code remaining.
