# CoinStack Database Enhancement Roadmap - Quick Wins

**Date**: January 31, 2026
**Source**: Database Architecture Analysis Report
**Focus**: High-impact, low-effort improvements for immediate value

---

## Analysis Summary

Current schema is **85-90% complete** for serious numismatics with excellent foundations:
- ✅ 139-column main table with comprehensive modeling
- ✅ Professional grading support (NGC/PCGS)
- ✅ 20 catalog reference systems with concordance
- ✅ LLM enrichment architecture
- ✅ Market intelligence and wishlist matching

**Key Insight**: The schema has world-class breadth but needs strategic depth in 3-4 specific areas to reach 95%+ completeness.

---

## 🎯 Recommended Enhancement Directions

### **Direction 1: Die Study Module** ⚡ HIGHEST PRIORITY

**Effort**: 2-3 days | **Impact**: ⭐⭐⭐⭐⭐ | **Risk**: Low

#### Why This Matters
- **Research Foundation**: Essential for scholarly die studies and variety identification
- **Rarity Assessment**: Shared dies reveal true scarcity (100 coins from 2 dies vs. 100 dies)
- **Market Intelligence**: Die varieties can have 10-100x price differences
- **Quick Win**: Only adds 2 new tables, no changes to existing schema

#### Implementation

**Step 1: Add Die Links Table** (1 hour)
```sql
CREATE TABLE die_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    die_id VARCHAR(100) NOT NULL,
    die_side VARCHAR(10) NOT NULL CHECK(die_side IN ('obverse', 'reverse')),
    coin_id_1 INTEGER NOT NULL REFERENCES coins_v2(id) ON DELETE CASCADE,
    coin_id_2 INTEGER NOT NULL REFERENCES coins_v2(id) ON DELETE CASCADE,
    confidence VARCHAR(20) DEFAULT 'certain' CHECK(confidence IN ('certain', 'probable', 'possible')),
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_die_link UNIQUE(die_id, coin_id_1, coin_id_2),
    CONSTRAINT chk_different_coins CHECK(coin_id_1 != coin_id_2)
);

CREATE INDEX ix_die_links_die_id ON die_links(die_id, die_side);
CREATE INDEX ix_die_links_coin1 ON die_links(coin_id_1);
CREATE INDEX ix_die_links_coin2 ON die_links(coin_id_2);
```

**Step 2: Add Die Varieties Table** (30 minutes)
```sql
CREATE TABLE die_varieties (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coin_id INTEGER NOT NULL REFERENCES coins_v2(id) ON DELETE CASCADE,
    variety_code VARCHAR(50) NOT NULL,              -- "RIC 207 var. a", "Crawford 443/1a"
    variety_description TEXT,
    distinguishing_features TEXT,                   -- "Reverse legend stops after AVG"
    reference_source VARCHAR(100),                  -- Source of variety classification
    die_pairing_notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_coin_variety UNIQUE(coin_id, variety_code)
);

CREATE INDEX ix_die_varieties_coin ON die_varieties(coin_id);
CREATE INDEX ix_die_varieties_code ON die_varieties(variety_code);
```

**Step 3: Domain Entity Enhancement** (2 hours)
```python
# backend/src/domain/coin.py - Add value object
@dataclass(frozen=True)
class DieVariety:
    """Represents a die variety classification."""
    variety_code: str
    variety_description: Optional[str] = None
    distinguishing_features: Optional[str] = None
    reference_source: Optional[str] = None
    die_pairing_notes: Optional[str] = None

# Add to Coin entity
@dataclass
class Coin:
    # ... existing fields ...
    die_varieties: List[DieVariety] = field(default_factory=list)
```

**Step 4: ORM Mapper Update** (2 hours)
```python
# backend/src/infrastructure/persistence/orm.py - Add model
class DieVarietyModel(Base):
    __tablename__ = "die_varieties"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    coin_id: Mapped[int] = mapped_column(Integer, ForeignKey("coins_v2.id"))
    variety_code: Mapped[str] = mapped_column(String(50))
    variety_description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    distinguishing_features: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reference_source: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    die_pairing_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    coin: Mapped["CoinModel"] = relationship(back_populates="die_varieties")

# Add to CoinModel
class CoinModel(Base):
    # ... existing fields ...
    die_varieties: Mapped[List[DieVarietyModel]] = relationship(
        back_populates="coin",
        cascade="all, delete-orphan"
    )
```

**Step 5: API Endpoint** (1 hour)
```python
# backend/src/infrastructure/web/routers/v2.py
@router.post("/coins/{coin_id}/die-varieties", response_model=CoinResponse)
async def add_die_variety(
    coin_id: int,
    variety: DieVarietyCreate,
    repo: ICoinRepository = Depends(get_coin_repository)
):
    """Add a die variety classification to a coin."""
    coin = repo.get_by_id(coin_id)
    if not coin:
        raise HTTPException(status_code=404, detail="Coin not found")

    # Add variety logic here
    # ...

    return CoinResponse.from_domain(coin)

@router.get("/coins/die-links/{die_id}", response_model=List[CoinResponse])
async def get_die_linked_coins(
    die_id: str,
    die_side: str,
    repo: ICoinRepository = Depends(get_coin_repository)
):
    """Get all coins sharing the same die."""
    # Query die_links table
    # Return coins with matching die_id
    pass
```

#### Immediate Use Cases Enabled
1. ✅ Track shared dies: "Show all coins from obverse die RIC_207_OBV_A"
2. ✅ Variety tracking: "This is RIC 207 var. a (legend stops after AVG)"
3. ✅ Rarity refinement: "100 RIC 207 coins but only 5 from this die pairing"
4. ✅ Research queries: "Find all die links for Severan denarii"

---

### **Direction 2: Attribution Confidence System** ⚡ QUICK WIN

**Effort**: 1-2 days | **Impact**: ⭐⭐⭐⭐ | **Risk**: Very Low

#### Why This Matters
- **Data Integrity**: Honest acknowledgment of attribution uncertainty
- **Research Transparency**: Track competing hypotheses for contested coins
- **Market Accuracy**: Uncertain attributions affect value
- **Quick Win**: One column + one table, minimal code changes

#### Implementation

**Step 1: Add Column to coins_v2** (30 minutes)
```sql
-- Alembic migration
ALTER TABLE coins_v2 ADD COLUMN attribution_certainty VARCHAR(20) DEFAULT 'certain'
    CHECK(attribution_certainty IN ('certain', 'probable', 'possible', 'tentative', 'contested', 'unknown'));

CREATE INDEX ix_coins_v2_attribution_certainty ON coins_v2(attribution_certainty);
```

**Step 2: Attribution Hypotheses Table** (1 hour)
```sql
CREATE TABLE attribution_hypotheses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coin_id INTEGER NOT NULL REFERENCES coins_v2(id) ON DELETE CASCADE,
    hypothesis_rank INTEGER NOT NULL DEFAULT 1,     -- 1 = primary, 2+ = alternatives

    -- Attribution fields
    issuer VARCHAR(100),
    issuer_term_id INTEGER REFERENCES vocab_terms(id),
    mint VARCHAR(100),
    mint_term_id INTEGER REFERENCES vocab_terms(id),
    year_start INTEGER,
    year_end INTEGER,
    denomination VARCHAR(50),

    -- Confidence and evidence
    confidence_score NUMERIC(3, 2) CHECK(confidence_score BETWEEN 0.0 AND 1.0),
    supporting_evidence TEXT,
    contrarian_evidence TEXT,
    source VARCHAR(200),                             -- Scholar, catalog, LLM

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT uq_coin_hypothesis_rank UNIQUE(coin_id, hypothesis_rank)
);

CREATE INDEX ix_attr_hyp_coin ON attribution_hypotheses(coin_id);
CREATE INDEX ix_attr_hyp_rank ON attribution_hypotheses(coin_id, hypothesis_rank);
```

**Step 3: Domain Enhancement** (2 hours)
```python
# backend/src/domain/coin.py - Add enums and value objects
class AttributionCertainty(str, Enum):
    CERTAIN = "certain"
    PROBABLE = "probable"
    POSSIBLE = "possible"
    TENTATIVE = "tentative"
    CONTESTED = "contested"
    UNKNOWN = "unknown"

@dataclass(frozen=True)
class AttributionHypothesis:
    """Alternative attribution hypothesis for contested coins."""
    hypothesis_rank: int
    issuer: Optional[str] = None
    mint: Optional[str] = None
    year_start: Optional[int] = None
    year_end: Optional[int] = None
    denomination: Optional[str] = None
    confidence_score: Optional[Decimal] = None
    supporting_evidence: Optional[str] = None
    contrarian_evidence: Optional[str] = None
    source: Optional[str] = None

# Add to Coin entity
@dataclass
class Coin:
    # ... existing fields ...
    attribution_certainty: AttributionCertainty = AttributionCertainty.CERTAIN
    attribution_hypotheses: List[AttributionHypothesis] = field(default_factory=list)
```

**Step 4: Audit Engine Enhancement** (1 hour)
```python
# backend/src/domain/services/audit_engine.py
class AuditEngine:
    def check_attribution_uncertainty(self, coin: Coin) -> List[str]:
        """Flag coins with uncertain attributions for review."""
        warnings = []

        if coin.attribution_certainty in [AttributionCertainty.TENTATIVE,
                                          AttributionCertainty.CONTESTED]:
            warnings.append(f"Attribution certainty is {coin.attribution_certainty.value}")

        if coin.attribution_certainty == AttributionCertainty.CONTESTED:
            if not coin.attribution_hypotheses:
                warnings.append("Contested attribution but no alternative hypotheses documented")

        return warnings
```

#### Immediate Use Cases Enabled
1. ✅ Honest cataloging: "Attribution to Hadrian is probable but not certain"
2. ✅ Research tracking: "Scholars debate whether this is Rome or Lugdunum mint"
3. ✅ Quality filters: "Show only coins with certain attributions"
4. ✅ Audit warnings: "5 coins marked contested need hypothesis documentation"

---

### **Direction 3: Variety Rarity Tracking** ⚡ MEDIUM WIN

**Effort**: 2-3 days | **Impact**: ⭐⭐⭐⭐ | **Risk**: Low

#### Why This Matters
- **Market Accuracy**: RIC 207 may be common, but RIC 207 var. a could be R5
- **Condition Rarity**: "Common type but rare in high grades"
- **Die Rarity**: "Only 3 known from this die pairing"
- **Extends Existing**: Builds on existing `rarity_assessments` table

#### Implementation

**Step 1: Extend rarity_assessments Schema** (1 hour)
```sql
-- Alembic migration to add columns
ALTER TABLE rarity_assessments ADD COLUMN variety_code VARCHAR(50);
ALTER TABLE rarity_assessments ADD COLUMN die_rarity_notes TEXT;
ALTER TABLE rarity_assessments ADD COLUMN condition_rarity_threshold VARCHAR(20);
    -- e.g., "EF" means "rare in EF or better"

-- Add indexes
CREATE INDEX ix_rarity_variety ON rarity_assessments(variety_code);
CREATE INDEX ix_rarity_grade_conditional ON rarity_assessments(
    catalog_system,
    catalog_number,
    grade_conditional
) WHERE grade_conditional IS NOT NULL;
```

**Step 2: Domain Value Object Enhancement** (1 hour)
```python
# backend/src/domain/coin.py
@dataclass(frozen=True)
class RarityAssessment:
    catalog_system: str                              # Existing
    catalog_number: str                              # Existing
    rarity_code: str                                 # Existing
    grade_conditional: Optional[str] = None          # Existing

    # NEW FIELDS
    variety_code: Optional[str] = None               # "var. a", "variant 1"
    die_rarity_notes: Optional[str] = None           # "Only 3 known from this die"
    condition_rarity_threshold: Optional[str] = None # "Rare in EF or better"

    source: Optional[str] = None                     # Existing
    notes: Optional[str] = None                      # Existing
```

**Step 3: Rarity Service Enhancement** (2 hours)
```python
# backend/src/domain/services/rarity_service.py (NEW)
class RarityService:
    """Service for rarity assessment and analysis."""

    def assess_variety_rarity(
        self,
        base_rarity: str,                           # "R2" for base type
        variety_multiplier: float                    # 0.1 = 10x rarer
    ) -> str:
        """Calculate variety rarity based on base type."""
        base_map = {"C": 0, "R": 1, "R2": 2, "R3": 3, "R4": 4, "R5": 5}

        if base_rarity not in base_map:
            return base_rarity

        adjusted = base_map[base_rarity] + (variety_multiplier * 2)
        adjusted = min(5, int(adjusted))  # Cap at R5

        return f"R{adjusted}" if adjusted > 0 else "C"

    def check_condition_rarity(
        self,
        coin_grade: str,
        threshold: str
    ) -> bool:
        """Check if coin meets condition rarity threshold."""
        grade_scale = {
            "Poor": 1, "Fair": 2, "AG": 3, "G": 4, "VG": 5, "F": 6, "VF": 7,
            "EF": 8, "AU": 9, "MS": 10, "MS+": 11
        }

        coin_level = grade_scale.get(coin_grade.split()[0], 0)
        threshold_level = grade_scale.get(threshold, 0)

        return coin_level >= threshold_level
```

**Step 4: UI Badge System** (Frontend, 1 hour)
```typescript
// frontend/src/components/coins/RarityBadge.tsx
interface RarityBadgeProps {
  baseRarity: string;
  varietyRarity?: string;
  conditionRarity?: boolean;
  dieRarity?: boolean;
}

export const RarityBadge: React.FC<RarityBadgeProps> = ({
  baseRarity,
  varietyRarity,
  conditionRarity,
  dieRarity
}) => {
  return (
    <div className="flex gap-1">
      <Badge variant={getRarityVariant(baseRarity)}>
        {baseRarity}
      </Badge>

      {varietyRarity && (
        <Badge variant="secondary" title="Variety Rarity">
          {varietyRarity} (var)
        </Badge>
      )}

      {conditionRarity && (
        <Badge variant="warning" title="Condition Rarity">
          Condition Rare
        </Badge>
      )}

      {dieRarity && (
        <Badge variant="info" title="Die Rarity">
          Die Rare
        </Badge>
      )}
    </div>
  );
};
```

#### Immediate Use Cases Enabled
1. ✅ Variety tracking: "RIC 207 is R2, but var. a is R4"
2. ✅ Condition rarity: "Common type but rare in EF or better"
3. ✅ Die rarity: "Only 5 known from this die combination"
4. ✅ Market intelligence: "Price premium justified by variety rarity"

---

### **Direction 4: Lightweight Iconography Start** ⚡ PROGRESSIVE WIN

**Effort**: 3-4 days (Phase 1), expandable | **Impact**: ⭐⭐⭐⭐ | **Risk**: Medium

#### Why This Matters
- **Thematic Searches**: "Show all coins with Victory on reverse"
- **Research Utility**: Group coins by deity, personification, or symbol
- **Progressive Enhancement**: Start simple, expand vocabulary over time
- **Quick Start**: Begin with 20-30 common types, grow organically

#### Implementation Strategy
Instead of building a complete taxonomy upfront (1-2 weeks), start with a minimal viable system:

**Step 1: Lightweight Iconography Table** (1 hour)
```sql
CREATE TABLE iconography_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tag_name VARCHAR(100) NOT NULL UNIQUE,          -- "Victory", "Mars", "Eagle"
    tag_category VARCHAR(50) NOT NULL,              -- deity, personification, animal, object, building
    tag_description TEXT,
    usage_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE coin_iconography_tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    coin_id INTEGER NOT NULL REFERENCES coins_v2(id) ON DELETE CASCADE,
    tag_id INTEGER NOT NULL REFERENCES iconography_tags(id) ON DELETE CASCADE,
    side VARCHAR(10) NOT NULL CHECK(side IN ('obverse', 'reverse', 'both')),
    position VARCHAR(50),                            -- center, left, right, field
    notes TEXT,
    CONSTRAINT uq_coin_tag UNIQUE(coin_id, tag_id, side)
);

CREATE INDEX ix_icon_tags_coin ON coin_iconography_tags(coin_id);
CREATE INDEX ix_icon_tags_tag ON coin_iconography_tags(tag_id);
CREATE INDEX ix_icon_tags_side ON coin_iconography_tags(side);
```

**Step 2: Seed Common Tags** (30 minutes)
```sql
-- Start with 30 most common Roman types
INSERT INTO iconography_tags (tag_name, tag_category, tag_description) VALUES
    ('Victory', 'personification', 'Winged female figure representing military victory'),
    ('Mars', 'deity', 'Roman god of war'),
    ('Jupiter', 'deity', 'King of gods, often with thunderbolt'),
    ('Eagle', 'animal', 'Legionary eagle or Jovian symbol'),
    ('Roma', 'personification', 'City personification with helmet'),
    ('Fortuna', 'deity', 'Goddess of fortune, often with rudder'),
    ('Concordia', 'personification', 'Harmony/agreement, often with patera'),
    ('Pax', 'personification', 'Peace, often with olive branch'),
    ('Sol', 'deity', 'Sun god with radiate crown'),
    ('Luna', 'deity', 'Moon goddess with crescent'),
    -- ... add 20 more common types
    ('Wreath', 'object', 'Laurel or oak wreath'),
    ('Trophy', 'object', 'Military trophy with armor'),
    ('Globe', 'object', 'World/cosmic sphere');
```

**Step 3: Domain Enhancement** (1 hour)
```python
# backend/src/domain/coin.py
@dataclass(frozen=True)
class IconographyTag:
    """Simple tag-based iconography tracking."""
    tag_name: str
    tag_category: str                    # deity, personification, animal, object
    side: str                            # obverse, reverse, both
    position: Optional[str] = None
    notes: Optional[str] = None

# Add to Coin entity
@dataclass
class Coin:
    # ... existing fields ...
    iconography_tags: List[IconographyTag] = field(default_factory=list)
```

**Step 4: Quick-Add API Endpoint** (2 hours)
```python
# backend/src/infrastructure/web/routers/v2.py
@router.post("/coins/{coin_id}/iconography-tags")
async def add_iconography_tags(
    coin_id: int,
    tags: List[IconographyTagCreate],
    repo: ICoinRepository = Depends(get_coin_repository)
):
    """Quick-add iconography tags to a coin."""
    # Validate tags exist
    # Add to coin_iconography_tags
    # Increment usage_count
    pass

@router.get("/iconography-tags/search")
async def search_iconography_tags(
    q: str,
    category: Optional[str] = None
):
    """Search available tags with autocomplete."""
    # FTS search on tag_name
    # Filter by category if provided
    pass

@router.get("/coins/by-iconography/{tag_name}")
async def get_coins_by_iconography(
    tag_name: str,
    side: Optional[str] = None
):
    """Find all coins with specific iconography."""
    # Query coin_iconography_tags
    # Return coins with matching tag
    pass
```

**Step 5: Frontend Tag Selector** (2 hours)
```typescript
// frontend/src/components/coins/IconographyTagSelector.tsx
import { useQuery } from '@tanstack/react-query';
import { Badge, Combobox } from '@/components/ui';

export const IconographyTagSelector: React.FC<{
  coinId: number;
  existingTags: IconographyTag[];
  onAdd: (tag: IconographyTag) => void;
}> = ({ coinId, existingTags, onAdd }) => {
  const { data: availableTags } = useQuery(['iconography-tags']);

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-2">
        {existingTags.map(tag => (
          <Badge key={tag.tag_name} variant="secondary">
            {tag.tag_name} ({tag.side})
          </Badge>
        ))}
      </div>

      <Combobox
        items={availableTags}
        onSelect={(tag) => onAdd(tag)}
        placeholder="Add iconography tag..."
      />
    </div>
  );
};
```

#### Progressive Expansion Path
- **Week 1**: 30 common tags, basic tagging UI
- **Month 1**: 100 tags, community contributions
- **Month 3**: 200+ tags, detailed attributes (Victory holding wreath vs. palm)
- **Month 6**: Full taxonomy with hierarchical categories

#### Immediate Use Cases Enabled
1. ✅ Basic thematic search: "Show all coins with Victory on reverse"
2. ✅ Deity collections: "All coins depicting Mars"
3. ✅ Symbol tracking: "Coins with eagles (legionary standards)"
4. ✅ Research queries: "Most common reverse types in Severan denarii"

---

## Implementation Priority Matrix

| Direction | Effort | Impact | Risk | Priority | Timeline |
|-----------|--------|--------|------|----------|----------|
| **1. Die Study** | 2-3 days | ⭐⭐⭐⭐⭐ | Low | 🔥 Highest | Week 1 |
| **2. Attribution Confidence** | 1-2 days | ⭐⭐⭐⭐ | Very Low | 🔥 High | Week 1-2 |
| **3. Variety Rarity** | 2-3 days | ⭐⭐⭐⭐ | Low | 🔶 Medium | Week 2-3 |
| **4. Iconography Start** | 3-4 days | ⭐⭐⭐⭐ | Medium | 🔶 Medium | Week 3-4 |

### Recommended Sprint Plan

**Sprint 1 (Week 1): Die Study Foundation**
- Days 1-2: Implement die_links and die_varieties tables
- Day 3: Domain and ORM mapping
- Day 4: API endpoints and testing
- Day 5: Frontend UI (basic die link display)

**Sprint 2 (Week 2): Attribution & Rarity**
- Days 1-2: Attribution confidence system
- Days 3-4: Variety rarity tracking
- Day 5: Integration testing and documentation

**Sprint 3 (Week 3): Iconography Start**
- Days 1-2: Lightweight iconography tables and seed data
- Days 3-4: API and frontend tag selector
- Day 5: User testing and refinement

---

## Success Metrics

### After Sprint 1 (Die Study)
- ✅ Can track shared dies across collection
- ✅ Can identify die varieties with notes
- ✅ Can query "all coins from die X"
- ✅ Research capability: 90% → 95%

### After Sprint 2 (Attribution & Rarity)
- ✅ Can mark attributions as uncertain
- ✅ Can document competing hypotheses
- ✅ Can track variety-specific rarity
- ✅ Data quality: 85% → 95%

### After Sprint 3 (Iconography)
- ✅ Can tag coins with 30+ common types
- ✅ Can search "all Victory reverses"
- ✅ Can group by deity/personification
- ✅ Discovery: 80% → 90%

### Overall Impact
**Database Completeness: 85% → 95%+** in 3-4 weeks

---

## Migration Safety Checklist

Before implementing any direction:

1. **Backup Database**
   ```bash
   cp backend/coinstack_v2.db backend/backups/coinstack_$(date +%Y%m%d_%H%M%S).db
   ```

2. **Create Alembic Migration**
   ```bash
   cd backend
   uv run alembic revision -m "Add die study tables"
   # Edit migration file
   uv run alembic upgrade head
   ```

3. **Test Rollback**
   ```bash
   uv run alembic downgrade -1
   uv run alembic upgrade head
   ```

4. **Unit Tests**
   ```bash
   uv run pytest tests/unit/domain/test_coin.py -v
   uv run pytest tests/unit/infrastructure/test_die_links.py -v
   ```

5. **Integration Tests**
   ```bash
   uv run pytest tests/integration/test_die_study.py -v
   ```

6. **Update Documentation**
   - `docs/ai-guide/05-DATA-MODEL.md` - Schema changes
   - `docs/ai-guide/07-API-REFERENCE.md` - New endpoints
   - `CLAUDE.md` - Quick reference updates

---

## Next Steps

1. **Review this roadmap** with project stakeholders
2. **Prioritize directions** based on current collection needs
3. **Start Sprint 1** (Die Study Module) - highest impact/lowest risk
4. **Iterate and refine** based on real-world usage

**Estimated Total Time**: 8-10 days for all 4 directions (can be parallelized)
**Expected Outcome**: Database completeness 85% → 95%+

---

**Document Version**: 1.0
**Last Updated**: January 31, 2026
**Status**: Ready for Implementation
