# Day 2: Repository Interfaces & Code Quality

**Date**: 2026-01-25
**Time Spent**: ~1.5 hours (so far)
**Status**: ✅ 2/3 CRITICAL TASKS COMPLETE

---

## Tasks Completed

### ✅ Task C3: Add Missing Repository Interfaces (1 hour)

**Objective**: Create Protocol interfaces for all repositories to enable dependency injection and testing.

**File**: `backend/src/domain/repositories.py`

**Changes**:
```python
# Added imports:
from src.domain.auction import AuctionLot
from src.domain.vocab import Issuer, Mint
from src.domain.series import Series, SeriesSlot

# Added 3 new repository interfaces:
class IAuctionDataRepository(Protocol):
    """Repository interface for auction data persistence."""
    def upsert(lot: AuctionLot, coin_id: Optional[int] = None) -> int
    def get_by_coin_id(coin_id: int) -> Optional[AuctionLot]
    def get_by_url(url: str) -> Optional[AuctionLot]
    def get_comparables(...) -> List[AuctionLot]

class ISeriesRepository(Protocol):
    """Repository interface for series/collection management."""
    def create(series: Series) -> Series
    def get_by_id(series_id: int) -> Optional[Series]
    def get_by_slug(slug: str) -> Optional[Series]
    def list_all(skip: int, limit: int) -> List[Series]
    def update(series: Series) -> Series
    def delete(series_id: int) -> bool

class IVocabRepository(Protocol):
    """Repository interface for vocabulary (issuers, mints)."""
    def get_issuer_by_id(issuer_id: int) -> Optional[Issuer]
    def get_issuer_by_name(canonical_name: str) -> Optional[Issuer]
    def create_issuer(issuer: Issuer) -> Issuer
    def list_issuers(...) -> List[Issuer]
    def get_mint_by_id(mint_id: int) -> Optional[Mint]
    def get_mint_by_name(canonical_name: str) -> Optional[Mint]
    def create_mint(mint: Mint) -> Mint
    def list_mints(...) -> List[Mint]
```

**Impact**:
- Enables loose coupling between layers
- Use cases can depend on interfaces instead of concrete implementations
- Enables dependency injection and mocking for tests
- Follows Clean Architecture principles

**Verification**: ✅ All 4 repository interfaces import successfully

**Next Steps** (Future Refactoring):
- Implement missing methods in existing repositories
- Update use cases to depend on interfaces
- Update dependencies.py to inject interfaces

---

### ✅ Task C4: Replace Bare Except Clauses (30 min)

**Objective**: Replace all bare `except:` clauses with specific exception types to prevent hiding critical errors.

**Problem**: Bare `except:` catches ALL exceptions including KeyboardInterrupt and SystemExit, making debugging impossible.

**Files Fixed** (5 bare except clauses):

#### 1. `backend/src/infrastructure/scrapers/ebay/scraper.py:90`
**Before**:
```python
async def _human_scroll(self, page):
    try:
        for _ in range(3):
            await page.evaluate(f'window.scrollBy(0, {random.randint(300, 700)})')
            await asyncio.sleep(random.uniform(0.5, 1.5))
    except:  # ❌ BAD
        pass
```

**After**:
```python
async def _human_scroll(self, page):
    try:
        for _ in range(3):
            await page.evaluate(f'window.scrollBy(0, {random.randint(300, 700)})')
            await asyncio.sleep(random.uniform(0.5, 1.5))
    except Exception as e:  # ✅ GOOD
        logger.warning(f"Human scroll simulation failed: {type(e).__name__}: {str(e)}")
        # Continue anyway - scrolling is nice-to-have for stealth
```

#### 2. `backend/src/infrastructure/scrapers/agora/parser.py:86`
**Before**:
```python
try:
    date_str = date_text.strip()
    # Simplify parsing logic or just leave as string if complex
    pass
except:  # ❌ BAD
    pass
```

**After**:
```python
try:
    date_str = date_text.strip()
    # TODO: Implement actual date parsing logic
    pass
except Exception as e:  # ✅ GOOD
    logger.warning(f"Failed to parse auction date '{date_text}': {type(e).__name__}: {str(e)}")
```

#### 3. `backend/src/infrastructure/scrapers/agora/parser.py:168`
**Before**:
```python
def _parse_price(self, price_str: str) -> Optional[float]:
    try:
        return float(price_str.replace(',', '').replace('$', ''))
    except:  # ❌ BAD
        return None
```

**After**:
```python
def _parse_price(self, price_str: str) -> Optional[float]:
    try:
        return float(price_str.replace(',', '').replace('$', ''))
    except (ValueError, AttributeError) as e:  # ✅ GOOD - specific exceptions
        logger.debug(f"Failed to parse price '{price_str}': {type(e).__name__}")
        return None
```

#### 4. `backend/src/infrastructure/scrapers/cng/scraper.py:55`
**Before**:
```python
try:
    await page.wait_for_selector('[class*="lot"]', timeout=10000)
except:  # ❌ BAD
    pass
```

**After**:
```python
try:
    await page.wait_for_selector('[class*="lot"]', timeout=10000)
except TimeoutError:  # ✅ GOOD - specific exception
    logger.warning(f"Timeout waiting for lot selector on {url}")
except Exception as e:
    logger.error(f"Error waiting for lot selector on {url}: {type(e).__name__}: {str(e)}")
```

#### 5. `backend/src/infrastructure/scrapers/biddr/scraper.py:57`
**Before**:
```python
try:
    await page.wait_for_selector(
        'h1, h2, .lot-info, [class*="lot"], [class*="description"]',
        timeout=10000
    )
except:  # ❌ BAD
    pass
```

**After**:
```python
try:
    await page.wait_for_selector(
        'h1, h2, .lot-info, [class*="lot"], [class*="description"]',
        timeout=10000
    )
except TimeoutError:  # ✅ GOOD - specific exception
    logger.warning(f"Timeout waiting for lot selector on {url}")
except Exception as e:
    logger.error(f"Error waiting for lot selector on {url}: {type(e).__name__}: {str(e)}")
```

**Impact**:
- **Before**: Errors hidden silently, impossible to debug
- **After**: All errors logged with context, KeyboardInterrupt/SystemExit not caught

**Verification**: ✅ No bare except clauses remain, all scrapers import successfully

**Patterns Used**:
1. Specific exceptions (ValueError, AttributeError, TimeoutError) when known
2. Generic `except Exception as e:` when exception type is unknown
3. Always log the exception with context
4. Never catch BaseException or bare except (allows Ctrl+C to work)

---

## Documentation Updates

### `CLAUDE.md`
Added new section: **Repository Interfaces**

```markdown
### Repository Interfaces
**Rule**: Always depend on repository interfaces (Protocols), never on concrete implementations.

**Available Interfaces** (`src/domain/repositories.py`):
- `ICoinRepository` - Coin persistence
- `IAuctionDataRepository` - Auction lot persistence
- `ISeriesRepository` - Series/collection management
- `IVocabRepository` - Vocabulary (issuers, mints)

**Why this matters**:
- Enables dependency injection and testing with mocks
- Loose coupling between layers (Clean Architecture)
- Can swap implementations without changing use cases
```

---

## Summary Statistics

| Metric | Value |
|--------|-------|
| **Time Spent** | 1.5 hours |
| **Tasks Completed** | 2/3 critical |
| **Files Modified** | 6 |
| **Lines Changed** | ~30 |
| **Repository Interfaces Created** | 3 |
| **Bare Except Clauses Fixed** | 5 |
| **Documentation Updated** | Yes (CLAUDE.md) |

---

## Impact Assessment

### Before Day 2
- ❌ No repository interfaces (tight coupling)
- ❌ Cannot mock repositories for testing
- ❌ Bare except clauses hide critical errors
- ❌ Impossible to debug scraper failures
- ❌ KeyboardInterrupt caught (Ctrl+C doesn't work)

### After Day 2
- ✅ 4 repository interfaces defined
- ✅ Can mock repositories for testing
- ✅ All exceptions logged with context
- ✅ Specific exception handling
- ✅ KeyboardInterrupt not caught (Ctrl+C works)

---

## Files Modified

1. `backend/src/domain/repositories.py` (+100 lines)
   - Added 3 repository interface imports
   - Added IAuctionDataRepository interface
   - Added ISeriesRepository interface
   - Added IVocabRepository interface

2. `backend/src/infrastructure/scrapers/ebay/scraper.py` (~3 lines)
   - Fixed bare except with Exception logging

3. `backend/src/infrastructure/scrapers/agora/parser.py` (~6 lines)
   - Fixed 2 bare except clauses with logging

4. `backend/src/infrastructure/scrapers/cng/scraper.py` (~4 lines)
   - Fixed bare except with TimeoutError handling

5. `backend/src/infrastructure/scrapers/biddr/scraper.py` (~4 lines)
   - Fixed bare except with TimeoutError handling

6. `CLAUDE.md` (+30 lines)
   - Added Repository Interfaces section

---

## Lessons Learned

1. **Bare Except is Evil**: Catches KeyboardInterrupt and SystemExit, making debugging impossible
2. **Specific Exceptions**: Use specific exception types when known (ValueError, TimeoutError)
3. **Always Log**: Even "silent" failures should be logged at debug/warning level
4. **Repository Interfaces**: Critical for Clean Architecture and testability
5. **Protocol vs ABC**: Python Protocols (PEP 544) are better than ABCs for structural typing

---

## Next Steps

### Remaining Day 2 Tasks
**C5: Standardize ORM Model Syntax** (3 hours) - Convert from legacy Column() to modern Mapped[T]

### Future Refactoring (Backlog)
1. Implement missing repository methods
2. Update existing services to implement repository interfaces
3. Update use cases to depend on interfaces
4. Update dependencies.py to inject interfaces
5. Add integration tests for repositories

---

## Verification Checklist

- [x] All repository interfaces import successfully
- [x] No bare except clauses in scrapers
- [x] All scrapers import successfully
- [x] Documentation updated (CLAUDE.md)
- [x] Exception handling with logging
- [x] KeyboardInterrupt not caught

---

**Status**: ✅ 2/3 CRITICAL TASKS COMPLETE
**Next**: C5 - Standardize ORM Model Syntax (3 hours)
**Progress**: On track for Day 2 completion
