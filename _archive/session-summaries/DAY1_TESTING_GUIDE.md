# Day 1 Morning - Testing & Verification Guide

**Date**: 2026-01-25
**Changes Made**: Database infrastructure fixes
**Time to Test**: ~15-20 minutes

---

## Overview of Changes

We made 4 critical infrastructure changes:
1. ✅ Created missing database tables (`coin_images_v2`, `auction_data_v2`)
2. ✅ Enabled foreign key constraints
3. ✅ Added 7 database indexes for performance
4. ✅ Created index management script

All changes are **non-breaking** and **backward compatible**. Your existing V2 code will work better with these fixes.

---

## Pre-Flight Checklist

Before testing, verify these files were modified:

```bash
cd C:\vibecode\coinstack

# 1. Check database backup exists
ls backend/backups/coinstack_v2_20260125_*.db
# Expected: Should show backup file ~84KB

# 2. Check modified files
git status
# Expected to see:
#   modified:   backend/src/infrastructure/persistence/database.py
#   modified:   CLAUDE.md
#   new file:   backend/src/infrastructure/scripts/add_indexes.py
#   new file:   REFACTORING_BACKLOG.md
#   new file:   V2_MIGRATION_PLAN.md
#   new file:   WEEK1_PROGRESS.md
#   new file:   DAY1_TESTING_GUIDE.md
```

---

## Test 1: Verify Database Tables Exist

### Step 1.1: Check tables via SQLite
```bash
cd backend
sqlite3 coinstack_v2.db ".tables"
```

**Expected Output**:
```
auction_data_v2  issuer_aliases   series           series_slots
coin_images_v2   issuers          series_memberships
coins_v2         mints
```

**✅ PASS IF**: You see `coin_images_v2` and `auction_data_v2` in the list

**❌ FAIL IF**: Tables are missing → Re-run `python -c "from src.infrastructure.persistence.database import init_db; init_db()"`

---

### Step 1.2: Check table schemas
```bash
cd backend
sqlite3 coinstack_v2.db "PRAGMA table_info(coin_images_v2);"
```

**Expected Output**:
```
0|id|INTEGER|0||1
1|coin_id|INTEGER|1||0
2|url|VARCHAR|1||0
3|image_type|VARCHAR|1||0
4|is_primary|BOOLEAN|0||0
```

```bash
sqlite3 coinstack_v2.db "PRAGMA table_info(auction_data_v2);"
```

**Expected Output**: Should show ~23 columns including:
- id, coin_id, url, source, lot_number
- hammer_price, estimate_low, estimate_high
- issuer, mint, year_start, year_end
- weight_g, diameter_mm, grade
- primary_image_url, additional_images

**✅ PASS IF**: All expected columns exist

---

### Step 1.3: Test table creation via Python
```bash
cd backend
python << 'EOF'
from src.infrastructure.persistence.database import Base, engine
from sqlalchemy import inspect

inspector = inspect(engine)
tables = inspector.get_table_names()

required_tables = ['coin_images_v2', 'auction_data_v2', 'coins_v2']
missing = [t for t in required_tables if t not in tables]

if missing:
    print(f"❌ FAIL: Missing tables: {missing}")
else:
    print("✅ PASS: All required tables exist")
    for table in required_tables:
        columns = [c['name'] for c in inspector.get_columns(table)]
        print(f"   {table}: {len(columns)} columns")
EOF
```

**Expected Output**:
```
✅ PASS: All required tables exist
   coin_images_v2: 5 columns
   auction_data_v2: 23 columns
   coins_v2: 27 columns
```

---

## Test 2: Verify Foreign Key Constraints

### Step 2.1: Check FK enforcement via SQLite CLI
```bash
cd backend
sqlite3 coinstack_v2.db "PRAGMA foreign_keys;"
```

**Expected Output**: `0`

**⚠️ NOTE**: This shows `0` because the CLI creates its own connection. This is EXPECTED behavior.

---

### Step 2.2: Check FK enforcement via SQLAlchemy (the real test)
```bash
cd backend
python << 'EOF'
from sqlalchemy import text
from src.infrastructure.persistence.database import engine

with engine.connect() as conn:
    result = conn.execute(text("PRAGMA foreign_keys")).fetchone()
    fk_enabled = bool(result[0])

    if fk_enabled:
        print("✅ PASS: Foreign keys ENABLED via SQLAlchemy")
        print("   All application code will enforce FK constraints")
    else:
        print("❌ FAIL: Foreign keys NOT enabled")
        print("   Event listener is not working")
EOF
```

**Expected Output**:
```
✅ PASS: Foreign keys ENABLED via SQLAlchemy
   All application code will enforce FK constraints
```

---

### Step 2.3: Test FK constraint enforcement (optional destructive test)
```bash
cd backend
python << 'EOF'
from sqlalchemy import text
from src.infrastructure.persistence.database import engine

print("Testing FK constraint enforcement...")
with engine.connect() as conn:
    try:
        # Try to insert coin_image with non-existent coin_id
        conn.execute(text("""
            INSERT INTO coin_images_v2 (coin_id, url, image_type, is_primary)
            VALUES (99999, 'test.jpg', 'obverse', 0)
        """))
        conn.commit()
        print("❌ FAIL: FK constraint NOT enforced (inserted orphan record)")
        # Cleanup
        conn.execute(text("DELETE FROM coin_images_v2 WHERE coin_id = 99999"))
        conn.commit()
    except Exception as e:
        if "FOREIGN KEY constraint failed" in str(e):
            print("✅ PASS: FK constraint properly enforced")
            print(f"   Got expected error: {type(e).__name__}")
        else:
            print(f"❌ FAIL: Unexpected error: {e}")
EOF
```

**Expected Output**:
```
Testing FK constraint enforcement...
✅ PASS: FK constraint properly enforced
   Got expected error: IntegrityError
```

---

## Test 3: Verify Database Indexes

### Step 3.1: List all indexes
```bash
cd backend
sqlite3 coinstack_v2.db "SELECT name, tbl_name FROM sqlite_master WHERE type='index' ORDER BY tbl_name, name;"
```

**Expected Output** (should include):
```
ix_coins_v2_acquisition_date|coins_v2
ix_coins_v2_category|coins_v2
ix_coins_v2_grading_state|coins_v2
ix_coins_v2_id|coins_v2
ix_coins_v2_issuer|coins_v2
ix_coins_v2_metal|coins_v2
ix_coins_v2_year_start|coins_v2
ix_issuers_canonical_name|issuers
ix_series_slug|series
ix_auction_data_v2_url|auction_data_v2
```

**✅ PASS IF**: You see indexes on coins_v2 (issuer, category, metal, year_start, etc.)

---

### Step 3.2: Run index verification script
```bash
cd backend
python -m src.infrastructure.scripts.add_indexes --verify
```

**Expected Output**:
```
============================================================
CoinStack V2 Database Index Creation
============================================================

Creating indexes on CoinStack V2 database...
⏭️  ix_coins_v2_issuer (already exists)
⏭️  ix_coins_v2_category (already exists)
⏭️  ix_coins_v2_metal (already exists)
[... more skipped ...]

📊 Summary:
   Created: 0
   Skipped: 10
   Total: 12

✅ All indexes already exist.

🔍 Verifying index usage with EXPLAIN QUERY PLAN...

Testing: category index
Query: SELECT * FROM coins_v2 WHERE category = 'imperial'
✅ Using index: SEARCH coins_v2 USING INDEX ix_coins_v2_category (category=?)

Testing: year_start index
Query: SELECT * FROM coins_v2 WHERE year_start >= -27 AND year_start <= 14
✅ Using index: SEARCH coins_v2 USING INDEX ix_coins_v2_year_start (year_start>? AND year_start<?)
```

**✅ PASS IF**:
- Summary shows "Skipped: 10" (or higher) - indexes already exist
- Query verification shows "Using index" for category and year_start

---

### Step 3.3: Performance comparison (if you have coins in DB)
```bash
cd backend
python << 'EOF'
from sqlalchemy import text
from src.infrastructure.persistence.database import engine
import time

with engine.connect() as conn:
    # Count coins
    count = conn.execute(text("SELECT COUNT(*) FROM coins_v2")).scalar()
    print(f"Testing with {count} coins in database\n")

    if count > 0:
        # Test 1: Query with index
        start = time.time()
        result = conn.execute(text("SELECT * FROM coins_v2 WHERE category = 'imperial'"))
        rows = result.fetchall()
        indexed_time = time.time() - start

        print(f"Query with index: {indexed_time*1000:.2f}ms ({len(rows)} results)")

        # Get query plan
        plan = conn.execute(text("EXPLAIN QUERY PLAN SELECT * FROM coins_v2 WHERE category = 'imperial'"))
        for row in plan:
            print(f"   Plan: {row[3]}")
    else:
        print("⚠️  No coins in database - skip performance test")
EOF
```

**Expected Output** (if coins exist):
```
Testing with 220 coins in database

Query with index: 0.52ms (112 results)
   Plan: SEARCH coins_v2 USING INDEX ix_coins_v2_category (category=?)
```

**✅ PASS IF**: Query plan shows "USING INDEX"

---

## Test 4: Application Integration Test

### Step 4.1: Test that backend starts without errors
```bash
cd backend
python -c "from src.infrastructure.web.main import app; print('✅ Backend imports successfully')"
```

**Expected Output**:
```
✅ Backend imports successfully
```

**❌ FAIL IF**: You see import errors or SQLAlchemy errors

---

### Step 4.2: Test database initialization
```bash
cd backend
python << 'EOF'
from src.infrastructure.persistence.database import init_db, SessionLocal
from src.infrastructure.persistence.orm import CoinModel, CoinImageModel, AuctionDataModel

print("Initializing database...")
init_db()

print("Testing session creation...")
db = SessionLocal()
try:
    # Test query
    count = db.query(CoinModel).count()
    print(f"✅ Database session works: {count} coins found")
finally:
    db.close()

print("✅ All database operations successful")
EOF
```

**Expected Output**:
```
Initializing database...
Testing session creation...
✅ Database session works: 220 coins found
✅ All database operations successful
```

---

### Step 4.3: Test scraper with auction data persistence (optional)
```bash
cd backend
python << 'EOF'
from src.infrastructure.persistence.database import SessionLocal
from src.infrastructure.persistence.orm import AuctionDataModel
from datetime import date
from decimal import Decimal

print("Testing auction data persistence...")
db = SessionLocal()
try:
    # Create test auction lot
    test_lot = AuctionDataModel(
        url="https://test.com/lot/12345",
        source="Test",
        lot_number="12345",
        hammer_price=Decimal("150.00"),
        currency="USD",
        issuer="Augustus",
        scraped_at=date.today()
    )

    db.add(test_lot)
    db.flush()

    lot_id = test_lot.id
    print(f"✅ Created test auction lot (ID: {lot_id})")

    # Query it back
    retrieved = db.query(AuctionDataModel).filter_by(id=lot_id).first()
    if retrieved and retrieved.issuer == "Augustus":
        print(f"✅ Retrieved auction lot successfully")
    else:
        print(f"❌ Failed to retrieve auction lot")

    # Cleanup
    db.delete(retrieved)
    db.commit()
    print("✅ Cleanup successful")

except Exception as e:
    print(f"❌ Test failed: {e}")
    db.rollback()
finally:
    db.close()
EOF
```

**Expected Output**:
```
Testing auction data persistence...
✅ Created test auction lot (ID: 1)
✅ Retrieved auction lot successfully
✅ Cleanup successful
```

---

## Test 5: Check Modified Code

### Step 5.1: Review database.py changes
```bash
cd backend/src/infrastructure/persistence
git diff database.py
```

**Expected Changes**:
1. Added model imports at top
2. Added `event` import from SQLAlchemy
3. Added FK pragma event listener

**Verify**:
- [ ] All 3 model files imported (`orm`, `models_vocab`, `models_series`)
- [ ] Event listener function exists
- [ ] `@event.listens_for(engine, "connect")` decorator present
- [ ] `cursor.execute("PRAGMA foreign_keys=ON")` in event listener

---

### Step 5.2: Verify index script exists
```bash
ls backend/src/infrastructure/scripts/add_indexes.py
cat backend/src/infrastructure/scripts/add_indexes.py | head -20
```

**Verify**:
- [ ] File exists
- [ ] Has proper imports
- [ ] Has `add_indexes()` function
- [ ] Has `verify_indexes()` function
- [ ] Can be run as module: `python -m src.infrastructure.scripts.add_indexes`

---

## Test 6: Backup & Rollback Test

### Step 6.1: Verify backup exists and is valid
```bash
cd backend
ls -lh backups/coinstack_v2_20260125_*.db
```

**Expected**: File ~84KB (same size as current coinstack_v2.db)

```bash
# Verify backup is a valid SQLite database
sqlite3 backups/coinstack_v2_20260125_*.db "SELECT COUNT(*) FROM coins_v2;"
```

**Expected**: Should return count of coins (e.g., 220)

**✅ PASS IF**: Backup opens and returns data

---

### Step 6.2: Test rollback procedure (DO NOT RUN unless needed)
```bash
# ⚠️ ONLY RUN IF YOU NEED TO ROLLBACK ⚠️
cd backend
cp coinstack_v2.db coinstack_v2_current.db  # Save current
cp backups/coinstack_v2_20260125_*.db coinstack_v2.db  # Restore backup
```

**To restore after testing rollback**:
```bash
cp coinstack_v2_current.db coinstack_v2.db
rm coinstack_v2_current.db
```

---

## Test Results Checklist

Mark each test as you complete it:

- [ ] **Test 1.1**: Tables visible in SQLite
- [ ] **Test 1.2**: Table schemas correct
- [ ] **Test 1.3**: Tables accessible from Python
- [ ] **Test 2.1**: FK pragma check (expected to show 0 in CLI)
- [ ] **Test 2.2**: FK enforcement via SQLAlchemy (must show 1)
- [ ] **Test 2.3**: FK constraint actually blocks invalid inserts
- [ ] **Test 3.1**: Indexes listed in SQLite
- [ ] **Test 3.2**: Index verification script passes
- [ ] **Test 3.3**: Performance test shows index usage
- [ ] **Test 4.1**: Backend imports successfully
- [ ] **Test 4.2**: Database initialization works
- [ ] **Test 4.3**: Auction data persistence works
- [ ] **Test 5.1**: Code review of database.py
- [ ] **Test 5.2**: Index script verified
- [ ] **Test 6.1**: Backup is valid

---

## Expected Test Results Summary

| Test Category | Expected Result | Critical? |
|--------------|----------------|-----------|
| Database Tables | All tables exist with correct schemas | **YES** |
| Foreign Keys | Enabled via SQLAlchemy (not CLI) | **YES** |
| Indexes | 7+ indexes created, queries use them | **YES** |
| Application | Backend imports without errors | **YES** |
| Backup | Valid SQLite database in backups/ | **YES** |

---

## Troubleshooting

### Problem: Tables don't exist
**Solution**:
```bash
cd backend
python -c "from src.infrastructure.persistence.database import init_db; init_db()"
```

### Problem: Foreign keys show 0 in SQLAlchemy test
**Solution**: Check that `database.py` has the event listener. Re-import and try again.

### Problem: Indexes don't exist
**Solution**:
```bash
cd backend
python -m src.infrastructure.scripts.add_indexes
```

### Problem: Backend won't start
**Solution**: Check for import errors:
```bash
cd backend
python -c "from src.infrastructure.persistence import orm, models_vocab, models_series; print('Imports OK')"
```

### Problem: Need to rollback everything
**Solution**:
```bash
cd backend
# Restore from backup
cp backups/coinstack_v2_20260125_002614.db coinstack_v2.db

# Revert code changes
git checkout backend/src/infrastructure/persistence/database.py
git clean -f backend/src/infrastructure/scripts/add_indexes.py
```

---

## After Testing

### If All Tests Pass ✅
You're ready to proceed with Day 1 Afternoon (critical bug fixes):
1. Fix `AuctionLot.additional_images` field
2. Fix `Coin.add_image()` logic
3. Fix repository field mapping
4. Fix transaction management

### If Tests Fail ❌
1. Note which tests failed
2. Check the error messages
3. Review the troubleshooting section
4. We can debug together before proceeding

### Optional: Commit Changes
```bash
git add -A
git commit -m "feat(db): add missing tables, enable FKs, create indexes

- Add coin_images_v2 and auction_data_v2 tables
- Enable foreign key constraints via event listener
- Create 7 critical indexes for query performance
- Add index management script with verification
- Update CLAUDE.md with database architecture
"
```

---

## Next Steps

After successful testing:
1. ✅ Mark Day 1 Morning as **COMPLETE**
2. 🚀 Begin Day 1 Afternoon - Domain & Repository Fixes
3. 📝 Update progress tracker

**Estimated testing time**: 15-20 minutes
**Your current status**: Phase 0, Day 1 Morning ✅ Ready for verification
