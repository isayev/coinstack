# System Architecture

## High-Level Overview

```mermaid
graph TB
    subgraph frontend [Frontend - React SPA]
        UI[React Components]
        TQ[TanStack Query]
        ZS[Zustand Stores]
    end
    
    subgraph backend [Backend - FastAPI]
        API[API Routers]
        SVC[Services]
        CRUD[CRUD Layer]
        ORM[SQLAlchemy Models]
    end
    
    subgraph external [External Services]
        OCRE[OCRE Catalog]
        CRRO[CRRO Catalog]
        RPC_CAT[RPC Catalog]
        AUCTIONS[Auction Sites]
        LLM[Anthropic LLM]
    end
    
    DB[(SQLite Database)]
    
    UI --> TQ
    TQ --> API
    ZS --> UI
    
    API --> SVC
    SVC --> CRUD
    CRUD --> ORM
    ORM --> DB
    
    SVC --> OCRE
    SVC --> CRRO
    SVC --> RPC_CAT
    SVC --> AUCTIONS
    SVC --> LLM
```

## Backend Architecture

### Layer Diagram

```mermaid
flowchart TD
    subgraph routers [Routers Layer - app/routers/]
        R1[coins.py]
        R2[import_export.py]
        R3[audit.py]
        R4[catalog.py]
        R5[scrape.py]
        R6[auctions.py]
        R7[stats.py]
    end
    
    subgraph services [Services Layer - app/services/]
        S1[excel_import.py]
        S2[reference_parser.py]
        S3[ngc_connector.py]
        S4[diff_enricher.py]
        
        subgraph catalogs [catalogs/]
            C1[ocre.py]
            C2[crro.py]
            C3[rpc.py]
        end
        
        subgraph scrapers [scrapers/]
            SC1[heritage.py]
            SC2[cng.py]
            SC3[biddr.py]
            SC4[ebay.py]
        end
        
        subgraph audit_svc [audit/]
            A1[audit_service.py]
            A2[auto_merge.py]
            A3[enrichment_service.py]
        end
    end
    
    subgraph crud [CRUD Layer - app/crud/]
        CR1[coin.py]
        CR2[auction.py]
        CR3[audit.py]
    end
    
    subgraph models [Models Layer - app/models/]
        M1[coin.py]
        M2[auction_data.py]
        M3[discrepancy.py]
        M4[enrichment.py]
    end
    
    DB[(SQLite)]
    
    routers --> services
    routers --> crud
    services --> crud
    crud --> models
    models --> DB
```

### Request Processing Flow

```mermaid
sequenceDiagram
    participant Client
    participant Router
    participant Service
    participant CRUD
    participant Model
    participant DB
    
    Client->>Router: HTTP Request
    Router->>Router: Validate with Pydantic
    Router->>Service: Business logic call
    Service->>CRUD: Data operation
    CRUD->>Model: SQLAlchemy query
    Model->>DB: SQL execution
    DB-->>Model: Result rows
    Model-->>CRUD: ORM objects
    CRUD-->>Service: Domain objects
    Service-->>Router: Processed result
    Router-->>Client: JSON Response
```

## Frontend Architecture

### Component Hierarchy

```mermaid
flowchart TD
    subgraph app [App.tsx]
        TP[ThemeProvider]
        QCP[QueryClientProvider]
        BR[BrowserRouter]
    end
    
    subgraph shell [AppShell]
        HD[Header]
        SB[Sidebar]
        CP[CommandPalette]
        ROUTES[Routes Outlet]
    end
    
    subgraph pages [Pages]
        P1[CollectionPage]
        P2[CoinDetailPage]
        P3[AddCoinPage]
        P4[EditCoinPage]
        P5[ImportPage]
        P6[AuditPage]
        P7[AuctionsPage]
        P8[StatsPage]
    end
    
    subgraph components [Component Groups]
        CG1[coins/ - CoinCard, CoinTable, CoinForm]
        CG2[audit/ - DiscrepancyCard, EnrichmentCard]
        CG3[layout/ - Header, Sidebar]
        CG4[ui/ - shadcn components]
        CG5[design-system/ - Badges, Indicators]
    end
    
    app --> shell
    shell --> pages
    pages --> components
```

### State Management

```mermaid
flowchart LR
    subgraph server_state [Server State - TanStack Query]
        Q1[useCoins]
        Q2[useAudit]
        Q3[useAuctions]
        Q4[useCatalog]
        Q5[useStats]
    end
    
    subgraph client_state [Client State - Zustand]
        Z1[uiStore - sidebar, viewMode]
        Z2[filterStore - filters, sort, pagination]
        Z3[columnStore - table columns]
    end
    
    API[Backend API]
    
    server_state <--> API
    Components --> server_state
    Components --> client_state
```

## Service Dependencies

### Catalog Services

```mermaid
flowchart TD
    REG[CatalogRegistry]
    
    subgraph catalogs [Catalog Services]
        OCRE[OCREService]
        CRRO[CRROService]
        RPC_SVC[RPCService]
    end
    
    BASE[CatalogService Base]
    
    REG --> OCRE
    REG --> CRRO
    REG --> RPC_SVC
    
    OCRE --> BASE
    CRRO --> BASE
    RPC_SVC --> BASE
    
    subgraph external [External APIs]
        E1[nomisma.org/OCRE]
        E2[numismatics.org/CRRO]
        E3[rpc.ashmus.ox.ac.uk]
    end
    
    OCRE --> E1
    CRRO --> E2
    RPC_SVC --> E3
```

**Catalog API URLs:**

| Service | Reference System | API Base URL |
|---------|-----------------|--------------|
| OCRE | RIC (Imperial) | http://numismatics.org/ocre/ |
| CRRO | Crawford (Republican) | http://numismatics.org/crro/ |
| RPC | RPC (Provincial) | https://rpc.ashmus.ox.ac.uk/ |

### Scraper Services

```mermaid
flowchart TD
    ORCH[AuctionOrchestrator]
    
    subgraph scrapers [Scraper Services]
        H[HeritageScraper]
        C[CNGScraper]
        B[BiddrScraper]
        E[EbayScraper]
        A[AgoraScraper]
    end
    
    BASE[AuctionScraperBase]
    BROWSER[BrowserScraper - Playwright]
    
    ORCH --> H
    ORCH --> C
    ORCH --> B
    ORCH --> E
    ORCH --> A
    
    H --> BASE
    C --> BASE
    B --> BASE
    E --> BASE
    
    H --> BROWSER
    C --> BROWSER
```

**Scraper Target URLs:**

| Scraper | Target URL |
|---------|------------|
| HeritageScraper | https://coins.ha.com |
| CNGScraper | https://cngcoins.com |
| BiddrScraper | https://biddr.com |
| EbayScraper | https://www.ebay.com |
| AgoraScraper | https://agoraauctions.com |

### Audit Services

```mermaid
flowchart TD
    AS[AuditService]
    
    subgraph audit_components [Audit Components]
        ES[EnrichmentService]
        AM[AutoMergeService]
        COMP[NumismaticComparator]
        CC[ConflictClassifier]
        TC[TrustConfig]
    end
    
    AS --> ES
    AS --> AM
    AS --> COMP
    AM --> TC
    COMP --> CC
    
    subgraph data [Data Models]
        AR[AuditRun]
        DISC[DiscrepancyRecord]
        ENR[EnrichmentRecord]
        FH[FieldHistory]
    end
    
    AS --> AR
    AS --> DISC
    ES --> ENR
    AM --> FH
```

## Database Layer

### Connection Flow

```mermaid
flowchart LR
    subgraph app [Application]
        REQ[Request]
        DEP[get_db dependency]
    end
    
    subgraph sqlalchemy [SQLAlchemy]
        ENG[Engine]
        SESS[SessionLocal]
        BASE[DeclarativeBase]
    end
    
    DB[(SQLite File)]
    
    REQ --> DEP
    DEP --> SESS
    SESS --> ENG
    ENG --> DB
    BASE --> ENG
```

### Key Entry Points

| Layer | Entry Point | File |
|-------|-------------|------|
| Backend | FastAPI app | `backend/app/main.py` |
| Database | Engine/Session | `backend/app/database.py` |
| Config | Settings | `backend/app/config.py` |
| Frontend | React app | `frontend/src/main.tsx` |
| Routes | Router setup | `frontend/src/App.tsx` |
| API Client | Axios | `frontend/src/lib/api.ts` |

## Key Architectural Patterns

### Backend Patterns

1. **Dependency Injection** - Database sessions via FastAPI `Depends()`
2. **Service Layer** - Business logic isolated from routers
3. **Repository Pattern** - CRUD functions abstract database operations
4. **Pydantic Validation** - Input/output schemas for all endpoints

### Frontend Patterns

1. **Server State** - TanStack Query manages API data
2. **Client State** - Zustand for UI-only state
3. **Colocation** - Hooks next to components that use them
4. **Composition** - Small, focused components assembled into pages

### Cross-Cutting Concerns

1. **Error Handling** - Global error handlers in FastAPI and Axios interceptors
2. **Caching** - TanStack Query with 5-minute stale time
3. **Persistence** - Zustand middleware for filterStore/columnStore
4. **CORS** - Configured for localhost development

---

**Previous:** [01-OVERVIEW.md](01-OVERVIEW.md) - Project overview  
**Next:** [03-BACKEND-MODULES.md](03-BACKEND-MODULES.md) - Backend module reference
