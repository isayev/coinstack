# Critical Rules & Requirements

**THESE RULES MUST BE FOLLOWED STRICTLY - NO EXCEPTIONS**

## Port Configuration (MANDATORY)

### Backend Port: 8000
```bash
# CORRECT - Always use port 8000 (backend uses uv)
cd backend && uv run run_server.py
```

### Frontend Port: 3000
```bash
# CORRECT - Always use port 3000
npm run dev  # Configured in vite.config.ts
```

### Port Conflicts
**NEVER** increment ports when busy. **ALWAYS** kill the conflicting process:

```powershell
# Windows PowerShell
Get-Process -Id (Get-NetTCPConnection -LocalPort 8000).OwningProcess | Stop-Process -Force
Get-Process -Id (Get-NetTCPConnection -LocalPort 3000).OwningProcess | Stop-Process -Force
```

**Or use the provided script**:
```powershell
.\restart.ps1  # Automatically kills ports and restarts servers
```

### Proxy Configuration
Frontend Vite dev server proxies `/api` to backend:

```typescript
// frontend/vite.config.ts - DO NOT CHANGE
export default defineConfig({
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

**Why This Matters**:
- Inconsistent ports break API communication
- Documentation and scripts assume these ports
- Multiple developers/sessions need predictable endpoints

## Git Authorship (MANDATORY)

### Author Configuration
**ALL commits MUST be authored by**:
```
isayev <olexandr@olexandrisayev.com>
```

### NO Co-authored-by Trailers
**WRONG**:
```
feat: add coin grading feature

Co-authored-by: Claude Sonnet 4.5 <noreply@anthropic.com>
```

**CORRECT**:
```
feat: add coin grading feature
```

### NO AI Assistance Mentions
**NEVER** mention AI assistance in:
- Commit messages
- Pull request descriptions
- Code comments
- Documentation

**Why This Matters**:
- All commits must reflect sole authorship by repository owner
- Professional git history
- Avoid attribution confusion

## Database Safety (MANDATORY)

### Database Location
```
backend/coinstack_v2.db  # Current canonical database
```

### REQUIRED Backup Before Schema Changes

**BEFORE** any operation that modifies schema:
1. **CREATE TIMESTAMPED BACKUP**:
```bash
# Format: coinstack_YYYYMMDD_HHMMSS.db
# Location: backend/backups/
cp backend/coinstack_v2.db backend/backups/coinstack_20260125_143022.db
```

2. **VERIFY BACKUP**:
```bash
# Check backup exists and has size > 0
ls -lh backend/backups/coinstack_20260125_143022.db
```

3. **THEN** proceed with schema change

### Operations Requiring Backup
- Adding/removing columns
- Changing column types
- Adding/removing tables
- Altering indexes
- Running migration scripts
- ANY DDL (Data Definition Language) operation

### Backup Retention
- **Keep rolling 5 backups**
- Delete oldest when creating 6th backup
- Never delete all backups

### Example Backup Script
```python
# backend/scripts/backup_database.py
from datetime import datetime
import shutil
from pathlib import Path

def backup_database():
    db_path = Path("backend/coinstack_v2.db")
    backup_dir = Path("backend/backups")
    backup_dir.mkdir(exist_ok=True)

    # Create timestamped backup
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = backup_dir / f"coinstack_{timestamp}.db"
    shutil.copy2(db_path, backup_path)
    print(f"Backup created: {backup_path}")

    # Keep only 5 most recent
    backups = sorted(backup_dir.glob("coinstack_*.db"))
    while len(backups) > 5:
        oldest = backups.pop(0)
        oldest.unlink()
        print(f"Deleted old backup: {oldest}")

if __name__ == "__main__":
    backup_database()
```

**Why This Matters**:
- SQLite has no built-in rollback for schema changes
- Data loss is catastrophic for collection management
- Backups enable recovery from failed migrations

## Scraper Usage (MANDATORY)

### ALWAYS Use Rich Scrapers

**Preferred scrapers** (Playwright-based with structured extraction):
- `backend/src/infrastructure/scrapers/heritage/scraper.py` (HeritageScraper)
- `backend/src/infrastructure/scrapers/cng/scraper.py` (CNGScraper)
- `backend/src/infrastructure/scrapers/biddr/scraper.py` (BiddrScraper)
- `backend/src/infrastructure/scrapers/ebay/scraper.py` (EBayScraper)
- `backend/src/infrastructure/scrapers/agora/scraper.py` (AgoraScraper)

**DO NOT USE** legacy/simple scrapers if rich version exists.

### Rich Scraper Features
- Playwright-based (handles JavaScript rendering)
- Structured data extraction into `AuctionLot` entities
- Image download and storage
- Provenance parsing
- Reference extraction
- Pagination handling
- Error recovery

### Example Usage
```python
from src.infrastructure.scrapers.heritage.scraper import HeritageScraper

scraper = HeritageScraper()
auction_lot = scraper.scrape_lot("https://coins.ha.com/itm/...")

# Returns AuctionLot entity with structured data
print(auction_lot.issuing_authority)
print(auction_lot.price_realized)
print(auction_lot.image_urls)
```

**Why This Matters**:
- Rich scrapers extract far more data
- Consistent data structure across auction houses
- Better error handling and resilience
- Image processing and storage

## Transaction Management (CRITICAL)

### Repositories NEVER Commit

**WRONG** - Repository commits:
```python
# src/infrastructure/repositories/coin_repository.py - WRONG
def save(self, coin: Coin) -> Coin:
    orm_coin = self._to_orm(coin)
    self.session.add(orm_coin)
    self.session.commit()  # ❌ NEVER do this
    return self._to_domain(orm_coin)
```

**CORRECT** - Repository uses flush():
```python
# src/infrastructure/repositories/coin_repository.py - CORRECT
def save(self, coin: Coin) -> Coin:
    orm_coin = self._to_orm(coin)
    merged = self.session.merge(orm_coin)
    self.session.flush()  # ✅ Get ID, don't commit
    return self._to_domain(merged)
```

### Automatic Transaction Management

Transactions are managed by `get_db()` dependency:

```python
# src/infrastructure/web/dependencies.py
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
        db.commit()  # Auto-commit on success
    except Exception:
        db.rollback()  # Auto-rollback on error
        raise
    finally:
        db.close()
```

**Why This Matters**:
- Multiple repository calls in one request = one transaction
- Exceptions automatically roll back ALL changes
- Repository doesn't control transaction boundaries
- Clean separation of concerns

## Dependency Injection (CRITICAL)

### Use Interfaces, Not Implementations

**WRONG** - Depending on concrete class:
```python
# src/application/commands/create_coin.py - WRONG
from src.infrastructure.repositories.coin_repository import SqlAlchemyCoinRepository

class CreateCoinUseCase:
    def __init__(self, repo: SqlAlchemyCoinRepository):  # ❌ Concrete class
        self.repo = repo
```

**CORRECT** - Depending on interface:
```python
# src/application/commands/create_coin.py - CORRECT
from src.domain.repositories import ICoinRepository  # Protocol

class CreateCoinUseCase:
    def __init__(self, repo: ICoinRepository):  # ✅ Interface
        self.repo = repo
```

### Available Repository Interfaces

**Location**: `src/domain/repositories.py`

```python
from typing import Protocol

class ICoinRepository(Protocol):
    """Repository interface for coins."""
    ...

class IAuctionDataRepository(Protocol):
    """Repository interface for auction data."""
    ...

class ISeriesRepository(Protocol):
    """Repository interface for series."""
    ...

class IVocabRepository(Protocol):
    """Repository interface for vocabulary."""
    ...
```

**Why This Matters**:
- Enables testing with mock repositories
- Loose coupling between layers
- Can swap implementations without changing use cases
- Core principle of Clean Architecture

## ORM Model Syntax (MANDATORY)

### Use SQLAlchemy 2.0 Syntax

**CORRECT** - Modern Mapped[T] syntax:
```python
from typing import Optional, List
from decimal import Decimal
from datetime import date
from sqlalchemy import Integer, String, Numeric, Date, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

class CoinModel(Base):
    __tablename__ = "coins_v2"

    # Required fields
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    category: Mapped[str] = mapped_column(String)
    weight_g: Mapped[Decimal] = mapped_column(Numeric(10, 2))

    # Optional fields
    issuer_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("issuers.id"), nullable=True)
    description: Mapped[Optional[str]] = mapped_column(String, nullable=True)

    # Relationships
    images: Mapped[List["CoinImageModel"]] = relationship(back_populates="coin")
    issuer_rel: Mapped[Optional["IssuerModel"]] = relationship()
```

**WRONG** - Legacy Column syntax:
```python
# DON'T USE THIS - OLD SYNTAX
class CoinModel(Base):
    __tablename__ = "coins_v2"

    id = Column(Integer, primary_key=True)  # ❌ Old syntax
    category = Column(String)
    images = relationship("CoinImageModel")  # ❌ No type hints
```

**Why This Matters**:
- Better type safety and IDE autocomplete
- mypy compatibility
- Modern SQLAlchemy 2.0 best practices
- Consistency with newer models

## N+1 Query Prevention (CRITICAL)

### ALWAYS Use Eager Loading

**WRONG** - Lazy loading causes N+1:
```python
# src/infrastructure/repositories/coin_repository.py - WRONG
def get_by_id(self, coin_id: int) -> Optional[Coin]:
    orm_coin = self.session.query(CoinModel).filter(
        CoinModel.id == coin_id
    ).first()  # ❌ Will lazy-load images with N queries

    return self._to_domain(orm_coin)
```

**CORRECT** - Eager loading with selectinload():
```python
# src/infrastructure/repositories/coin_repository.py - CORRECT
from sqlalchemy.orm import selectinload

def get_by_id(self, coin_id: int) -> Optional[Coin]:
    orm_coin = self.session.query(CoinModel).options(
        selectinload(CoinModel.images)  # ✅ Eager load in 1 query
    ).filter(CoinModel.id == coin_id).first()

    return self._to_domain(orm_coin)
```

**Performance Impact**:
- Without eager loading: 1 query + N queries = O(n)
- With eager loading: 1 query + 1 query = O(1)
- 10-100x faster with large collections

**Why This Matters**:
- Critical for collection list performance
- Coin detail page loads faster
- API endpoints remain responsive

## Testing Requirements (MANDATORY)

### Backend Test Markers

**ALL backend tests MUST be marked**:

```python
import pytest

@pytest.mark.unit
def test_coin_validation():
    """Unit test - fast, no DB."""
    coin = Coin(category="imperial", ...)
    errors = coin.validate()
    assert len(errors) == 0

@pytest.mark.integration
def test_coin_repository_save(db_session):
    """Integration test - uses DB."""
    repo = SqlAlchemyCoinRepository(db_session)
    coin = Coin(...)
    saved = repo.save(coin)
    assert saved.id is not None
```

### Running Tests
```bash
# Run unit tests only (fast)
pytest -m unit

# Run integration tests only (slower)
pytest -m integration

# Run all tests
pytest tests -p pytest_asyncio
```

**Why This Matters**:
- Unit tests run fast (TDD feedback loop)
- Integration tests verify real DB operations
- CI can run unit tests first, integration later
- Clear separation of test types

## Import Path Standards (CRITICAL)

### Backend Imports Use `src.` Prefix

**CORRECT**:
```python
from src.domain.coin import Coin
from src.domain.repositories import ICoinRepository
from src.infrastructure.persistence.orm import CoinModel
from src.infrastructure.web.dependencies import get_db
```

**WRONG**:
```python
from domain.coin import Coin  # ❌ Missing src. prefix
from backend.src.domain.coin import Coin  # ❌ Includes backend/
```

### Frontend Imports Use `@/` Alias

**CORRECT**:
```typescript
import { CoinCard } from '@/components/coins/CoinCard'
import { useCoins } from '@/hooks/useCoins'
import { Coin } from '@/domain/schemas'
```

**WRONG**:
```typescript
import { CoinCard } from '../../../components/coins/CoinCard'  // ❌ Relative paths
import { useCoins } from 'hooks/useCoins'  // ❌ No alias
```

**Why This Matters**:
- Consistent import paths across codebase
- Easier refactoring (no relative path updates)
- Better IDE autocomplete

## BC/AD Date Handling (CRITICAL)

### Years Are Signed Integers

**Rules**:
- AD years: Positive integers (e.g., `14` = 14 AD)
- BC years: Negative integers (e.g., `-44` = 44 BC)
- Year 0: Does NOT exist (1 BC → 1 AD directly)

**Example**:
```python
# Julius Caesar coins: 49-44 BC
coin.mint_year_start = -49
coin.mint_year_end = -44

# Augustus coins: 27 BC - 14 AD
coin.mint_year_start = -27
coin.mint_year_end = 14
```

### Chronological Sorting
```python
# Sort chronologically (NOT numerically)
coins = sorted(coins, key=lambda c: c.mint_year_start or 9999)

# Result: -49 (49 BC), -27 (27 BC), 14 (14 AD), 98 (98 AD)
```

**Why This Matters**:
- Standard numismatic convention
- Enables chronological sorting
- Simplifies date range queries

## Documentation Requirements (MANDATORY)

### BEFORE Making Changes

**MUST consult relevant guides in `docs/ai-guide/`**:

| Change Type | Read First |
|-------------|------------|
| Backend logic | `03-BACKEND-MODULES.md`, `08-CODING-PATTERNS.md` |
| Domain entities | `04-DOMAIN-ENTITIES.md`, `05-DATA-MODEL.md` |
| Frontend components | `11-FRONTEND-COMPONENTS.md`, `10-DESIGN-SYSTEM.md` |
| UI/Design | `10-DESIGN-SYSTEM.md` |
| API endpoints | `07-API-REFERENCE.md` |
| Database schema | `05-DATA-MODEL.md` |

### AFTER Making Changes

**MUST update documentation to reflect changes**:

| Change Made | Update This Guide |
|-------------|-------------------|
| New/modified API endpoint | `07-API-REFERENCE.md` |
| New database field | `05-DATA-MODEL.md` |
| New backend module | `03-BACKEND-MODULES.md` |
| New domain entity | `04-DOMAIN-ENTITIES.md` |
| New/modified component | `11-FRONTEND-COMPONENTS.md` |
| Design token change | `10-DESIGN-SYSTEM.md` |
| New hook or store | `04-FRONTEND-MODULES.md` |
| Data flow change | `06-DATA-FLOWS.md` |
| New pattern | `08-CODING-PATTERNS.md` |

**Why This Matters**:
- Documentation is the source of truth for the codebase
- Outdated docs lead to inconsistent implementations
- AI assistants rely on accurate docs for context
- New contributors need accurate reference

---

## Validation Summary Checklist

Before committing code, verify:

### Ports & Configuration
- [ ] Backend on port 8000, frontend on port 3000
- [ ] Git author is `isayev <olexandr@olexandrisayev.com>`
- [ ] No Co-authored-by trailers or AI mentions

### Database
- [ ] Database backup created before schema changes
- [ ] Repositories use `flush()` not `commit()`
- [ ] Repository methods use `selectinload()` for relationships

### Architecture
- [ ] Use cases depend on interfaces (Protocol), not concrete classes
- [ ] ORM models use `Mapped[T]` and `mapped_column()` syntax
- [ ] Rich scrapers used (not legacy)

### Code Style
- [ ] Backend imports use `src.` prefix
- [ ] Frontend imports use `@/` alias
- [ ] BC years stored as negative integers
- [ ] Backend tests marked with `@pytest.mark.unit` or `@pytest.mark.integration`

### Documentation (MANDATORY)
- [ ] Consulted relevant `docs/ai-guide/` before changes
- [ ] Updated relevant guides after making changes
- [ ] Documentation reflects current implementation

---

**Next:** [09-CODING-PATTERNS.md](09-CODING-PATTERNS.md) - Common coding patterns and idioms
