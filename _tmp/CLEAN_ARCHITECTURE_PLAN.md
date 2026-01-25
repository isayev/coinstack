# CoinStack: Clean Architecture Refactoring Plan

## Vision
To transform CoinStack from a coupled, monolithic application into a modular, testable system using **Clean Architecture** (Hexagonal Architecture) principles.

## Core Principles
1.  **Dependency Rule**: Source code dependencies only point inwards. Domain code knows nothing about the DB or the Web.
2.  **Testability**: Business rules can be tested without the UI, Database, or Web Server.
3.  **Separation of Concerns**: Distinct layers for Domain (Entities), Application (Use Cases), and Infrastructure (Frameworks).

## Directory Structure
```
backend/
├── src/
│   ├── domain/              # Pure Python - NO dependencies
│   │   ├── coin.py          # Entities & Value Objects
│   │   └── repositories.py  # Interfaces (Ports)
│   ├── application/         # Orchestration logic
│   │   ├── commands/        # Write operations (Use Cases)
│   │   └── queries/         # Read operations
│   ├── infrastructure/      # Framework implementations
│   │   ├── persistence/     # SQLAlchemy models & repos
│   │   └── web/             # FastAPI routers
│   └── interface/           # CLI / API definitions
└── tests/
    ├── unit/                # Fast, runs in <1s
    └── integration/         # Slower, uses in-memory DB
```

## Phased Implementation Roadmap

### Phase 1: The Domain Core (Current Focus)
**Goal**: Establish the "Walking Skeleton" of the new architecture.

*   [x] **P1-01**: Define `Coin` Aggregate Root (Pure Python Entity).
*   [x] **P1-02**: Define `ICoinRepository` Interface.
*   [x] **P1-03**: Implement `SqlAlchemyCoinRepository` (Adapter).
*   [x] **P1-04**: Implement `CreateCoinUseCase` (Application Layer).
*   [x] **P1-05**: Setup TDD Infrastructure (`conftest.py`, `pytest`).

### Phase 2: Refactoring the "God Object"
**Goal**: Deconstruct the 72-field `Coin` model into composed Value Objects.

*   [ ] **P2-01**: Define `GradingDetails` Value Object (Service, Grade, Strike, Surface).
*   [ ] **P2-02**: Define `AcquisitionDetails` Value Object (Price, Source, Date).
*   [ ] **P2-03**: Update `Coin` entity to use these VOs.
*   [ ] **P2-04**: Update `SqlAlchemyCoinRepository` to map VOs to DB columns (using SQLAlchemy Composites or flat mapping).

### Phase 3: The Audit Engine
**Goal**: Decouple Audit logic from the Database.

*   [ ] **P3-01**: Define `AuditStrategy` Interface in Domain.
*   [ ] **P3-02**: Implement Strategies (`GradeDiscrepancyStrategy`, `AttributionStrategy`).
*   [ ] **P3-03**: Create `RunAuditUseCase` that accepts a `Coin` and `AuctionData` and returns a `AuditResult` (Pure Logic).
*   [ ] **P3-04**: Implement Infrastructure Adapter to fetch Auction Data.

### Phase 4: Import/Export Adapters
**Goal**: Remove procedural scripts.

*   [ ] **P4-01**: Define `ICollectionImporter` Interface (Port).
*   [ ] **P4-02**: Implement `ExcelImporter` (Adapter using openpyxl).
*   [ ] **P4-03**: Create `ImportCollectionUseCase`.

### Phase 5: API Migration (Strangler Fig)
**Goal**: Switch API endpoints to use new Use Cases without breaking frontend.

*   [ ] **P5-01**: Create new router `routers/v2/coins.py`.
*   [ ] **P5-02**: Endpoint `POST /api/v2/coins` calls `CreateCoinUseCase`.
*   [ ] **P5-03**: Point Frontend to V2 endpoints incrementally.

## TDD Workflow
For every task:
1.  **Write a Failing Test** in `tests/unit/` (for logic) or `tests/integration/` (for DB).
2.  **Implement Domain Logic** (if applicable).
3.  **Implement Infrastructure/Adapter** (if applicable).
4.  **Refactor** to ensure Clean Code.
5.  **Verify** test passes.

## Metrics for Success
*   **Test Coverage**: >80% on new `src/` code.
*   **Domain Purity**: 0 imports from `sqlalchemy` or `fastapi` in `src/domain`.
*   **Coupling**: High Cohesion, Low Coupling (verified by simple imports).
