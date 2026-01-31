# TODO: Numismatic Enhancements (Phase 1.5)

> **Source**: Agent review of Phase 1 implementation (2026-01-31)
> **Priority**: Medium - Enhancements for world-class cataloging

These enhancements were identified during the Phase 1 verification to improve support for professional numismatic cataloging.

---

## 1. Attribution Enhancements

### Additional Authority Types

**File**: `backend/src/domain/coin.py` - `AuthorityType` enum

Add the following values:
```python
class AuthorityType(str, Enum):
    # Existing
    MAGISTRATE = "magistrate"
    SATRAP = "satrap"
    DYNAST = "dynast"
    STRATEGOS = "strategos"
    ARCHON = "archon"
    EPISTATES = "epistates"
    # NEW: Add these
    PROCURATOR = "procurator"     # Judaea (Pontius Pilate, Felix)
    PREFECT = "prefect"           # Roman Egypt prefects
    LEGATE = "legate"             # Legati Augusti (legionary coinages)
    TETRARCH = "tetrarch"         # Herodian dynasties
    ETHNARCH = "ethnarch"         # Jewish ethnarchs
    QUAESTOR = "quaestor"         # Quaestores pro praetore
    PRAETOR = "praetor"           # Republican mints
    MONARCH = "monarch"           # Independent kings on Greek coins
```

### Additional Portrait Relationships

**File**: `backend/src/domain/coin.py` - `PortraitRelationship` enum

Add the following values:
```python
class PortraitRelationship(str, Enum):
    # Existing
    SELF = "self"
    CONSORT = "consort"
    HEIR = "heir"
    PARENT = "parent"
    PREDECESSOR = "predecessor"
    COMMEMORATIVE = "commemorative"
    DIVUS = "divus"
    DIVA = "diva"
    # NEW: Add these
    SIBLING = "sibling"           # Byzantine joint reigns
    ANCESTOR = "ancestor"         # Coins showing Alexander centuries later
    ADOPTIVE_PARENT = "adoptive_parent"  # Roman succession (Hadrian/Trajan)
    DEITY = "deity"               # Greek issues with Athena, Apollo
    PERSONIFICATION = "personification"  # Roma, Constantinople
```

---

## 2. Physical Enhancements

### Additional Weight Standards

**File**: `backend/src/domain/coin.py` - `WeightStandard` enum

Add the following values:
```python
class WeightStandard(str, Enum):
    # Existing
    ATTIC = "attic"
    AEGINETAN = "aeginetan"
    CORINTHIAN = "corinthian"
    PHOENICIAN = "phoenician"
    DENARIUS_EARLY = "denarius_early"
    DENARIUS_REFORMED = "denarius_reformed"
    ANTONINIANUS = "antoninianus"
    # NEW: Add these (critical for proper cataloging)
    PTOLEMAIC = "ptolemaic"       # Egyptian standard
    CHIAN = "chian"               # Ionia
    MILESIAN = "milesian"         # Archaic Greek
    EUBOIC = "euboic"             # Related to Attic
    PERSIC = "persic"             # Persian/Achaemenid
    RHODIAN = "rhodian"           # Rhodes, Caria
    SOLIDUS = "solidus"           # Byzantine gold (4.5g nominal)
    FOLLIS_REFORM = "follis_reform"  # Diocletianic reform
    SILIQUA = "siliqua"           # Late Roman silver
    TREMISSIS = "tremissis"       # 1/3 solidus
```

### Additional Flan Shapes

**File**: `backend/src/domain/coin.py` - `FlanShape` enum

```python
class FlanShape(str, Enum):
    # Existing
    ROUND = "round"
    IRREGULAR = "irregular"
    OVAL = "oval"
    SQUARE = "square"
    SCYPHATE = "scyphate"
    # NEW: Add these
    RECTANGULAR = "rectangular"    # Archaic Greek issues
    INCUSE_SQUARE = "incuse_square"  # Archaic Magna Graecia
```

### Revised Flan Type

**File**: `backend/src/domain/coin.py` - `FlanType` enum

Note: "hammered" is redundant with "struck" for ancient coins. Consider:
```python
class FlanType(str, Enum):
    CAST = "cast"
    STRUCK = "struck"
    CUT_FROM_BAR = "cut_from_bar"
    # Replace 'hammered' with more useful distinctions:
    DUMP = "dump"                 # Thick, small diameter (late Roman AE4)
    SPREAD = "spread"             # Thin, spread flan (Celtic imitations)
    SERRATED = "serrated"         # Denarii serrati
```

---

## 3. Countermark Support (NEW FEATURE)

**Priority**: HIGH - Essential for Roman Provincial cataloging

### Database Schema

Add to migration:
```sql
-- Countermarks (official re-validations, distinct from banker's marks)
ALTER TABLE coins_v2 ADD COLUMN has_countermark BOOLEAN DEFAULT FALSE;
ALTER TABLE coins_v2 ADD COLUMN countermark_description TEXT;
ALTER TABLE coins_v2 ADD COLUMN countermark_authority TEXT;  -- Who applied it
ALTER TABLE coins_v2 ADD COLUMN countermark_type TEXT;  -- 'imperial', 'legionary', 'civic'
```

### Domain Value Object

**File**: `backend/src/domain/coin.py`

```python
@dataclass(frozen=True, slots=True)
class Countermark:
    """Official countermark (distinct from banker's marks)."""
    has_countermark: bool = False
    description: str | None = None  # "AVG in rectangular punch"
    authority: str | None = None    # "Vespasian", "Legio X"
    countermark_type: str | None = None  # 'imperial', 'legionary', 'civic'
```

---

## 4. TPG Grading Enhancements

### NGC Strike/Surface Grades

**File**: `backend/src/domain/coin.py` - `GradingTPGEnhancements`

```python
@dataclass(frozen=True, slots=True)
class GradingTPGEnhancements:
    # Existing
    grade_numeric: int | None = None
    grade_designation: str | None = None
    has_star_designation: bool = False
    photo_certificate: bool = False
    verification_url: str | None = None
    # NEW: Add these
    strike_grade: int | None = None   # NGC Strike grade (1-5 scale)
    surface_grade: int | None = None  # NGC Surface grade (1-5 scale)
    is_fine_style: bool = False       # NGC Fine Style designation
```

### Additional Grade Designations

Document supported values:
- 'Fine Style' (FS)
- 'Choice' (Ch)
- 'Gem'
- 'Superb Gem'
- 'Prooflike' (PL)
- 'Proof' (PF)
- 'Specimen' (SP)
- 'Plus' (+) modifier

---

## 5. Additional Strike Quality Field

**Priority**: Medium - Separate from grading assessment

### Database Schema

```sql
ALTER TABLE coins_v2 ADD COLUMN strike_quality_detail TEXT;
-- Values: 'sharp', 'soft', 'flat', 'double_struck', 'off_metal', 'brockage'

ALTER TABLE coins_v2 ADD COLUMN is_double_struck BOOLEAN DEFAULT FALSE;
ALTER TABLE coins_v2 ADD COLUMN is_brockage BOOLEAN DEFAULT FALSE;
```

---

## 6. Edge Type Field

**Priority**: Medium - Important for serrated denarii

### Database Schema

```sql
ALTER TABLE coins_v2 ADD COLUMN edge_type TEXT;
-- Values: 'plain', 'reeded', 'serrated', 'incuse_legend', 'decorated'

ALTER TABLE coins_v2 ADD COLUMN edge_inscription TEXT;
```

---

## 7. Centering Enhancement

### Numeric Centering Scores

Industry standard (NGC/PCGS use numeric scoring):

```python
@dataclass(frozen=True, slots=True)
class Centering:
    centering: str | None = None  # Existing categorical
    centering_notes: str | None = None
    # NEW: Add numeric scores
    obverse_centering_score: int | None = None  # 1-5 scale
    reverse_centering_score: int | None = None  # 1-5 scale
```

---

## 8. Fourree/Plated Coin Detection

**Priority**: Low - Specialized for authentication

```python
@dataclass(frozen=True, slots=True)
class PlatingDetails:
    """For fourrees and plated coins."""
    core_visible: bool = False
    plating_intact_pct: int | None = None  # 0-100%
    plating_metal: str | None = None  # Original plating metal
```

---

## 9. Corrosion Tracking

**Priority**: Low - Conservation documentation

```python
@dataclass(frozen=True, slots=True)
class CorrosionDetails:
    corrosion_type: str | None = None  # 'none', 'bronze_disease', 'horn_silver', 'pitting'
    is_stabilized: bool = False  # Bronze disease treatment status
    corrosion_notes: str | None = None
```

---

## Implementation Order

1. **Phase 1.5a** (Quick wins - enum additions only):
   - Add missing enum values (AuthorityType, PortraitRelationship, WeightStandard)
   - No schema migration needed

2. **Phase 1.5b** (New fields requiring migration):
   - Countermark support
   - Edge type field
   - Strike quality detail

3. **Phase 1.5c** (TPG enhancements):
   - NGC Strike/Surface grades
   - Fine Style designation
   - Numeric centering scores

4. **Future** (Low priority):
   - Plating detection
   - Corrosion tracking

---

## Files to Update

| Component | Files |
|-----------|-------|
| Domain enums | `backend/src/domain/coin.py` |
| ORM model | `backend/src/infrastructure/persistence/orm.py` |
| Migration | `backend/alembic/versions/YYYYMMDD_phase1_5_numismatic.py` |
| Mapper | `backend/src/infrastructure/mappers/coin_mapper.py` |
| API models | `backend/src/infrastructure/web/routers/v2.py` |
| Frontend schemas | `frontend/src/domain/schemas.ts` |
| Form components | `frontend/src/components/coins/CoinForm/*.tsx` |

---

## 10. Phase 6 Collections Enhancements

> **Source**: Numismatic domain expert review of Phase 6 implementation (2026-01-31)
> **Status**: Current implementation APPROVED for production use

### Display Order Persistence

**Priority**: Medium - User experience enhancement

Current behavior: Custom display order is stored in `collection_coins.custom_order` but needs frontend UI support for drag-and-drop reordering.

**Implementation**:
- Add drag-and-drop reordering in collection view
- Call `PUT /api/v2/collections/{id}/coins/order` with new order
- Consider optimistic UI updates for responsiveness

**Files to update**:
- `frontend/src/components/collections/CollectionCoinsGrid.tsx` (new)
- `frontend/src/hooks/useCollections.ts` - `useReorderCollectionCoins` already exists

### Completion Progress Visualization

**Priority**: Medium - Type set collectors feature

For type set collections (`is_type_set=true`), display visual progress toward completion.

**Implementation**:
1. **Progress bar component**: Show `completion_percentage` with visual indicator
2. **Type slot grid**: Display defined types from `type_set_definition` with:
   - Filled slots (coins with `fulfills_type` matching)
   - Empty slots (missing types)
   - Placeholder indicators (coins with `is_placeholder=true`)
3. **Statistics panel**: Display breakdown from `/api/v2/collections/{id}/stats`

**Files to create**:
- `frontend/src/components/collections/TypeSetProgress.tsx`
- `frontend/src/components/collections/TypeSlotGrid.tsx`
- `frontend/src/components/collections/CollectionStatsPanel.tsx`

### Collection Cover Coin Display

**Priority**: Low - Visual enhancement

Use `cover_coin_id` to display a featured coin image as the collection thumbnail in grid views.

**Implementation**:
- Fetch coin image from `/api/v2/coins/{cover_coin_id}` when displaying collection cards
- Fallback to first coin in collection if no cover coin set
- Allow user to set cover coin via context menu on any coin in collection

---

**Created**: 2026-01-31
**Source**: Numismatic domain expert agent review
**Updated**: 2026-01-31 - Added Phase 6 Collections enhancements
