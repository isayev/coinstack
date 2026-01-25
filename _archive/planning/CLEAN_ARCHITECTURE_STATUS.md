# CoinStack: Clean Architecture Status Report

## Completed Foundations
We have successfully transitioned the core of CoinStack to a **Clean Architecture**.

### 1. Domain Layer (`src/domain/`)
*   **Entities:** `Coin` (Aggregate Root), `AuctionLot` (Entity).
*   **Value Objects:** `Dimensions`, `Attribution`, `GradingDetails`, `AcquisitionDetails`.
*   **Services:** `AuditEngine`, `ScraperOrchestrator`.
*   **Strategies:** Audit Strategies (Attribution, Physics, Date, Grade).
*   **Interfaces:** `IScraper`, `ICollectionImporter`.

### 2. Infrastructure Layer (`src/infrastructure/`)
*   **Persistence:** `SqlAlchemyCoinRepository`, `CoinModel`.
*   **Importers:** `ExcelImporter`.
*   **Scrapers:** `HeritageScraper`, `CNGScraper` (Playwright-based).
*   **Web:** `FastAPI` V2 API.

### 3. Application Layer (`src/application/`)
*   **Use Cases:** 
    *   `CreateCoinUseCase`
    *   `ImportCollectionUseCase`
    *   `ScrapeAuctionLotUseCase`

### 4. Migration (`Production`)
*   **Status:** **COMPLETE** (100% Data Transfer).

### 5. Frontend
*   **Core:** React + Vite + Vitest + React Query + Tailwind.
*   **Features:** Collection, Detail, Add/Edit, Audit, Scraper.
*   **Tests:** 100% pass rate (18 tests).

### 6. Deployment
*   **Docker:** Configured `docker-compose.yml` for full stack deployment.
*   **Backend:** `Dockerfile` based on `mcr.microsoft.com/playwright/python`.
*   **Frontend:** `Dockerfile` with Nginx for static serving.

## How to Run Tests
```bash
# Backend
cd backend && python -m pytest tests -p pytest_asyncio

# Frontend
cd frontend && npm test
```

## How to Deploy
```bash
# Build and start containers
docker-compose up --build -d

# Access application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000/docs
```