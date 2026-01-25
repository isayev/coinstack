# AI Guide V2 Migration - Complete

**Date**: 2026-01-25
**Status**: Phase 1 Complete ✅

## Summary

Successfully migrated CoinStack AI developer documentation from V1 (backend/app/) to V2 (backend/src/) Clean Architecture. All critical files updated with V2 paths, Clean Architecture principles, and mandatory requirements.

## Files Created (New V2 Documentation)

### ✅ 02-CLEAN-ARCHITECTURE.md
**Purpose**: Comprehensive guide to V2 Clean Architecture
**Content**:
- Domain/Application/Infrastructure layer responsibilities
- Dependency Rule (dependencies flow inward)
- Repository interfaces (Protocols)
- Dependency injection flow
- Benefits and anti-patterns
- V1 → V2 migration comparison

### ✅ 04-DOMAIN-ENTITIES.md
**Purpose**: Complete domain entity reference
**Content**:
- Core entities: Coin, AuctionLot, Series, VocabTerm
- Value objects: Dimensions, Attribution, GradingDetails, AcquisitionDetails
- Enums: Category, Metal, Rarity, GradeService
- Related entities: CoinImage, CoinReference
- Domain services: AuditEngine, SearchService

### ✅ 06-FILE-LOCATIONS.md
**Purpose**: Quick file/directory lookup reference
**Content**:
- Complete directory tree (domain/application/infrastructure)
- Task-to-file mapping (adding fields, endpoints, scrapers)
- Command reference (tests, servers, builds)
- File naming conventions
- Quick paths for common operations

### ✅ 08-CRITICAL-RULES.md
**Purpose**: Mandatory requirements (STRICT ENFORCEMENT)
**Content**:
- Port configuration (8000 backend, 3000 frontend) - MANDATORY
- Git authorship (isayev, no Co-authored-by) - MANDATORY
- Database backups before schema changes - MANDATORY
- Rich scraper usage - REQUIRED
- Transaction management (flush not commit) - CRITICAL
- Dependency injection (interfaces not implementations) - CRITICAL
- ORM syntax (SQLAlchemy 2.0 Mapped[T]) - MANDATORY
- N+1 prevention (selectinload) - CRITICAL
- Validation checklist

## Files Updated (V1 → V2 Migration)

### ✅ 03-BACKEND-MODULES.md
**Changes**:
- Removed all V1 paths (backend/app/)
- Updated to V2 structure (backend/src/)
- Added Domain/Application/Infrastructure layer documentation
- Documented repository pattern with Protocols
- Showed proper ORM models (SQLAlchemy 2.0 syntax)
- Added use case examples
- Covered web layer with FastAPI routers
- Included scraper implementations

### ✅ README.md
**Changes**:
- Updated project structure to V2 (backend/src/)
- Changed all file paths to V2
- Added Clean Architecture section
- Highlighted critical rules
- Updated command examples (src.infrastructure.web.main:app)
- Added V1 archive note
- Reorganized document index
- Added architecture highlights

### ✅ CLAUDE.md (Root Project File)
**Changes**:
- Added comprehensive ai-guide/ reference section
- Linked to all new documentation files
- Organized by category (Architecture, Development, API, Tasks, Systems)
- Preserved all critical rules

## Files Deleted (Obsolete V1)

### ❌ 02-ARCHITECTURE.md
**Reason**: Replaced by 02-CLEAN-ARCHITECTURE.md
**Issues**:
- Used V1 paths (backend/app/)
- Showed old architecture (routers → services → crud → models)
- Didn't reflect Clean Architecture layers
- Mermaid diagrams referenced V1 structure

## Files Requiring Further Review (Phase 2)

These files exist but need V2 compliance verification:

### 📋 04-FRONTEND-MODULES.md
- May have outdated component references
- Check API client paths
- Verify hook examples

### 📋 05-DATA-MODEL.md
- ERD may need V2 table updates
- Check if models_vocab.py and models_series.py are documented
- Verify ORM syntax examples

### 📋 06-DATA-FLOWS.md
- Check if flows reflect Clean Architecture
- Update sequence diagrams if showing V1 paths

### 📋 07-API-REFERENCE.md
- Large file, needs endpoint verification
- Check for V1 router paths
- Update to show v2.py, vocab.py, series.py routers

### 📋 08-CODING-PATTERNS.md
- Verify examples use V2 patterns
- Check repository pattern examples
- Ensure transaction management is correct

### 📋 09-TASK-RECIPES.md
- Update step-by-step guides with V2 paths
- Verify file locations in recipes

### 📋 01-OVERVIEW.md
- Already mostly V2 compliant (checked earlier)
- Minor updates may be needed

## Key Achievements

### 1. Clean Architecture Documentation
- Comprehensive explanation of Domain/Application/Infrastructure layers
- Clear dependency rules (dependencies flow inward)
- Repository pattern with Protocol interfaces
- Value objects and aggregate roots documented

### 2. Critical Rules Enforcement
- Mandatory requirements clearly documented
- Port standards (8000/3000) enforced
- Git authorship rules explicit
- Database safety procedures defined
- Transaction management patterns specified

### 3. File Navigation Aid
- Complete directory tree for V2
- Task-to-file mapping for common operations
- Quick command reference
- File naming conventions

### 4. Domain Knowledge Capture
- All entities documented (Coin, AuctionLot, Series, VocabTerm)
- Value objects with immutability patterns
- Enums with all valid values
- Domain services and strategies

## Validation Checklist

Before committing code, AI assistants should verify:

- [ ] Backend on port 8000, frontend on port 3000
- [ ] Git author is `isayev <olexandr@olexandrisayev.com>`
- [ ] No Co-authored-by trailers or AI mentions
- [ ] Database backup created before schema changes
- [ ] Rich scrapers used (not legacy)
- [ ] Repositories use `flush()` not `commit()`
- [ ] Use cases depend on interfaces (Protocol), not concrete classes
- [ ] ORM models use `Mapped[T]` and `mapped_column()` syntax
- [ ] Repository methods use `selectinload()` for relationships
- [ ] Backend tests marked with `@pytest.mark.unit` or `@pytest.mark.integration`
- [ ] Backend imports use `src.` prefix
- [ ] Frontend imports use `@/` alias
- [ ] BC years stored as negative integers

## Impact on AI Assistants

### Before Migration
- Confused by V1 paths (backend/app/) that don't exist in V2
- Unclear on Clean Architecture principles
- No reference for repository interfaces vs implementations
- Missing transaction management rules
- No guidance on mandatory requirements (ports, git, backups)

### After Migration
- Clear V2 path structure (backend/src/)
- Comprehensive Clean Architecture guide
- Repository pattern documented with Protocols
- Transaction management explicit (flush not commit)
- Critical rules enforced with validation checklist
- Quick file lookup reference
- Complete domain entity documentation

## Next Steps (Phase 2)

1. Review and update remaining files:
   - 04-FRONTEND-MODULES.md
   - 05-DATA-MODEL.md
   - 06-DATA-FLOWS.md
   - 07-API-REFERENCE.md
   - 08-CODING-PATTERNS.md
   - 09-TASK-RECIPES.md

2. Consider additional documentation:
   - Testing patterns (unit vs integration)
   - Scraper development guide
   - Vocabulary system guide
   - Series management guide
   - Frontend state management guide

3. Add code examples:
   - Complete use case implementations
   - Repository implementations
   - Scraper implementations
   - Frontend hooks and components

## File Statistics

**Created**: 5 files (02-CLEAN-ARCHITECTURE.md, 04-DOMAIN-ENTITIES.md, 06-FILE-LOCATIONS.md, 08-CRITICAL-RULES.md, MIGRATION_COMPLETE.md)
**Updated**: 3 files (03-BACKEND-MODULES.md, README.md, CLAUDE.md)
**Deleted**: 1 file (02-ARCHITECTURE.md)
**Total Lines**: ~3,500+ lines of V2 documentation

## Conclusion

Phase 1 migration is complete. AI assistants now have comprehensive, V2-compliant documentation covering:
- Clean Architecture principles
- Domain entities and value objects
- Critical mandatory requirements
- File locations and navigation
- Backend module structure
- Project overview and quick start

All core V2 concepts are documented. Phase 2 will focus on updating remaining files and adding specialized guides.

---

**Migration completed by**: Claude Code (Sonnet 4.5)
**Adhering to**: CLAUDE.md requirements (no AI mentions in git commits)
