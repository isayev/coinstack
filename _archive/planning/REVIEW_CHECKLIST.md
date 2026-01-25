# Day 1 Morning - Review Checklist

Quick reference for reviewing changes before continuing.

---

## 🔍 Files to Review (2 modified, 6 created)

### Modified Files

#### 1. `backend/src/infrastructure/persistence/database.py`
**Lines Changed**: +12 lines
**Changes**:
- Added 3 model imports (orm, models_vocab, models_series)
- Added SQLAlchemy event import
- Added FK pragma event listener (7 lines)

**Review Focus**:
```python
# Lines 4-8: Model imports
from src.infrastructure.persistence import orm
from src.infrastructure.persistence import models_vocab
from src.infrastructure.persistence import models_series

# Lines 17-23: FK enforcement
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
```

**Questions to Ask**:
- ✅ Are all ORM model modules imported?
- ✅ Is the event listener correctly attached to engine?
- ✅ Will this affect existing connections?

---

#### 2. `CLAUDE.md`
**Lines Changed**: +63 lines
**Changes**:
- Added "Database Architecture (V2)" section
- Documented FK enforcement
- Documented index strategy
- Documented transaction management rules
- Added 2 new gotchas

**Review Focus**: Lines 210-272 (new section before "Common Gotchas")

**Questions to Ask**:
- ✅ Is the documentation clear for future developers?
- ✅ Are the code examples correct?
- ✅ Do the transaction management rules match our implementation?

---

### New Files Created

#### 3. `backend/src/infrastructure/scripts/add_indexes.py`
**Size**: 172 lines
**Purpose**: Creates database indexes with verification

**Review Focus**:
```python
# Key features to verify:
def add_indexes():
    # 1. Creates 12 indexes (idempotent with IF NOT EXISTS)
    # 2. Checks existing indexes before creating
    # 3. Reports summary statistics

def verify_indexes():
    # 1. Tests query plans with EXPLAIN QUERY PLAN
    # 2. Verifies indexes are actually being used
```

**Questions to Ask**:
- ✅ Can this script be run multiple times safely?
- ✅ Does it handle errors gracefully?
- ✅ Is the verification logic sound?

---

#### 4. `backend/backups/coinstack_v2_20260125_002614.db`
**Size**: 84KB
**Purpose**: Pre-migration backup

**Review Focus**:
- File exists and is valid SQLite database
- Contains all data from before changes

**Test**: `sqlite3 backups/coinstack_v2_20260125_002614.db "SELECT COUNT(*) FROM coins_v2;"`

---

#### 5. `REFACTORING_BACKLOG.md`
**Size**: 1,200+ lines
**Purpose**: Prioritized list of 30 items to fix

**Review Focus**:
- Priority 0 (Blockers): 6 items, 5 hours
- Priority 1 (Critical): 6 items, 145 hours
- Priority 2 (High): 6 items, 180 hours
- Priority 3-4 (Medium/Low): 12 items, 148 hours

**Questions to Ask**:
- ✅ Are priorities correct?
- ✅ Are time estimates reasonable?
- ✅ Are critical items actually critical?

---

#### 6. `V2_MIGRATION_PLAN.md`
**Size**: 1,800+ lines
**Purpose**: 12-week step-by-step migration plan

**Review Focus**:
- Phase 0: Foundation (Week 1)
- Phase 1: Critical Features (Weeks 2-5)
- Phase 2: Feature Parity (Weeks 6-9)
- Phase 3: Production Ready (Weeks 10-12)

**Questions to Ask**:
- ✅ Is the timeline realistic?
- ✅ Are dependencies between phases clear?
- ✅ Is the incremental approach sound?

---

#### 7. `WEEK1_PROGRESS.md`
**Size**: ~400 lines
**Purpose**: Daily progress tracking

**Review Focus**: Summary statistics, impact assessment, lessons learned

---

#### 8. `DAY1_TESTING_GUIDE.md` (this file)
**Size**: ~500 lines
**Purpose**: Step-by-step testing instructions

---

## 🧪 Quick Tests to Run (5 minutes)

### Test 1: Verify Tables Exist
```bash
cd backend
sqlite3 coinstack_v2.db "SELECT name FROM sqlite_master WHERE type='table' AND name IN ('coin_images_v2', 'auction_data_v2');"
```
**Expected**: Both table names returned

---

### Test 2: Verify FK Enforcement
```bash
cd backend
python -c "from sqlalchemy import text; from src.infrastructure.persistence.database import engine; conn = engine.connect(); result = conn.execute(text('PRAGMA foreign_keys')).fetchone(); print(f'FK Enabled: {bool(result[0])}')"
```
**Expected**: `FK Enabled: True`

---

### Test 3: Verify Indexes
```bash
cd backend
sqlite3 coinstack_v2.db "SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND name LIKE 'ix_coins_v2_%';"
```
**Expected**: At least 6 (issuer, category, metal, year_start, acquisition_date, grading_state)

---

### Test 4: Verify Backend Still Starts
```bash
cd backend
python -c "from src.infrastructure.web.main import app; print('✅ Backend loads successfully')"
```
**Expected**: `✅ Backend loads successfully`

---

### Test 5: Verify Backup
```bash
cd backend
ls -lh backups/coinstack_v2_20260125_*.db
```
**Expected**: File ~84KB in size

---

## 📋 Review Questions

### Architecture
- [ ] Do the changes follow Clean Architecture principles?
- [ ] Are infrastructure changes properly isolated?
- [ ] Will these changes affect existing code?

### Database
- [ ] Is the FK enforcement approach correct?
- [ ] Are the indexes on the right columns?
- [ ] Will indexes improve performance for typical queries?

### Safety
- [ ] Is the backup strategy sound?
- [ ] Can we rollback if needed?
- [ ] Are changes non-breaking?

### Documentation
- [ ] Is CLAUDE.md accurate and helpful?
- [ ] Are code examples correct?
- [ ] Will future developers understand these changes?

### Testing
- [ ] Are the test instructions clear?
- [ ] Can someone else run these tests?
- [ ] Do tests cover all critical changes?

---

## 🚨 Red Flags to Watch For

### During Testing
- ❌ Import errors when loading backend
- ❌ SQLAlchemy errors about missing tables
- ❌ Foreign keys showing as disabled in SQLAlchemy
- ❌ No indexes created
- ❌ Backend won't start

### In Code Review
- ❌ Circular imports
- ❌ Hardcoded values (should use config)
- ❌ Missing error handling
- ❌ Unclear comments or documentation

---

## ✅ Sign-Off Checklist

Before proceeding to Day 1 Afternoon:

### Testing
- [ ] Ran all 5 quick tests - all passed
- [ ] Reviewed testing guide - no failures
- [ ] Tested with actual application - works correctly

### Code Review
- [ ] Reviewed `database.py` changes - looks good
- [ ] Reviewed `add_indexes.py` script - logic is sound
- [ ] Reviewed CLAUDE.md updates - documentation is clear

### Safety
- [ ] Backup exists and is valid
- [ ] Know how to rollback if needed
- [ ] Changes are non-breaking

### Understanding
- [ ] Understand what each change does
- [ ] Understand why each change was needed
- [ ] Understand the impact of each change

### Planning
- [ ] Reviewed REFACTORING_BACKLOG.md - priorities make sense
- [ ] Reviewed V2_MIGRATION_PLAN.md - timeline is reasonable
- [ ] Ready to proceed to next phase

---

## 🎯 Decision Point

### ✅ All Tests Pass & Reviews Complete
**Action**: Proceed to Day 1 Afternoon
- Fix critical bugs (4 items, ~2 hours)
- Continue with migration plan

### ⚠️ Some Concerns or Questions
**Action**: Discuss and clarify before proceeding
- Review specific concerns
- Make adjustments if needed
- Re-test after changes

### ❌ Tests Failing or Major Issues
**Action**: Debug and fix before proceeding
- Identify root cause
- Apply fixes
- Re-run tests
- Do not proceed until issues resolved

---

## 📞 Next Steps Communication

**If proceeding**: "All tests passed. Continue with Day 1 Afternoon bug fixes."

**If concerns**: "Tests passed but I have questions about [specific area]."

**If issues**: "Test [X] failed with [error]. Need to debug before continuing."

---

**Current Status**: Awaiting review & testing
**Time Required**: 15-20 minutes for thorough review and testing
**Risk Level**: LOW (all changes are infrastructure improvements)
