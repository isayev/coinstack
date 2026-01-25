# Coin Series & Collection Management

> **Phase 2.5 Addition** - Insert after P2-05 (Reference Normalization)

## Overview

Coin series are fundamental to numismatic collecting. This feature provides comprehensive series management including canonical series (Twelve Caesars), user-defined series, smart/dynamic series, completion tracking, gap analysis, and wishlist integration.

---

## Feature Requirements

### Series Types

| Type | Description | Example |
|------|-------------|---------|
| **Canonical** | Well-known numismatic series with defined membership | Twelve Caesars, Five Good Emperors |
| **Reference-based** | All coins from a catalog section | RIC I Augustus, Crawford 44 |
| **Dynastic** | Coins grouped by ruling dynasty | Julio-Claudian, Flavian, Severan |
| **Thematic** | Coins sharing iconographic elements | Animals, Architecture, Deities |
| **Geographic** | Coins from specific mints/regions | Eastern Mints, Gallic Empire |
| **User-defined** | Personal collecting goals | "My Republican Denarii" |
| **Smart/Dynamic** | Auto-populated based on filter criteria | "All silver coins > 3g" |
| **Hierarchical** | Nested series | Roman Imperial > Julio-Claudian > Augustus > Lugdunum |

### Core Functionality

1. **Series Management**
   - Create, edit, delete series
   - Import from templates/presets
   - Clone and customize existing series
   - Archive completed series

2. **Membership Management**
   - Manual coin assignment
   - Bulk assignment via filters
   - Auto-assignment for smart series
   - Slot-based membership (specific positions)

3. **Completion Tracking**
   - Progress visualization (8/12 Caesars)
   - Slot status (owned, wanted, not targeted)
   - Quality tiers (basic, upgrade wanted, museum quality)
   - Multiple specimens per slot

4. **Gap Analysis**
   - Missing items identification
   - Rarity/difficulty assessment
   - Price estimation for gaps
   - Acquisition suggestions

5. **Wishlist Integration**
   - Series gaps → automatic wishlist
   - Priority ranking
   - Budget allocation per series
   - Alert triggers for gap fills

6. **Visualization**
   - Grid/gallery view by series
   - Completion dashboard
   - Timeline view (chronological)
   - Map view (geographic series)

---

## Data Model

### Core Tables

```python
# models/series.py
"""
Coin series and collection management models.
"""

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, Float,
    Enum, ForeignKey, JSON, Index, CheckConstraint, UniqueConstraint
)
from sqlalchemy.orm import relationship
from datetime import datetime
from enum import Enum as PyEnum

from app.database import Base


class SeriesType(str, PyEnum):
    """Types of coin series."""
    CANONICAL = "canonical"       # Well-known standard series
    REFERENCE = "reference"       # Based on catalog reference
    DYNASTIC = "dynastic"         # Dynasty-based grouping
    THEMATIC = "thematic"         # Theme-based (animals, gods, etc.)
    GEOGRAPHIC = "geographic"     # Mint/region based
    TEMPORAL = "temporal"         # Time period based
    USER_DEFINED = "user_defined" # Custom user series
    SMART = "smart"               # Dynamic filter-based


class SlotStatus(str, PyEnum):
    """Status of a series slot."""
    EMPTY = "empty"               # No coin assigned, not actively seeking
    WANTED = "wanted"             # Gap - actively seeking
    FILLED = "filled"             # Have a coin
    UPGRADE_WANTED = "upgrade"    # Have one, want better
    NOT_TARGETED = "not_targeted" # Intentionally skipping this slot
    MULTIPLE = "multiple"         # Collecting multiple examples


class Series(Base):
    """
    A collection series grouping related coins.
    
    Can be canonical (Twelve Caesars), reference-based (RIC I),
    user-defined, or smart (dynamic filter-based).
    """
    __tablename__ = "series"
    __table_args__ = (
        Index('ix_series_type', 'series_type'),
        Index('ix_series_active', 'is_active'),
        CheckConstraint('target_count IS NULL OR target_count > 0'),
    )
    
    id = Column(Integer, primary_key=True)
    
    # Identity
    name = Column(String(200), nullable=False)
    slug = Column(String(100), unique=True, index=True)  # URL-friendly identifier
    description = Column(Text)
    
    # Classification
    series_type = Column(Enum(SeriesType), nullable=False, default=SeriesType.USER_DEFINED)
    category = Column(String(50))  # "imperial", "republican", "provincial", "greek"
    
    # Hierarchy (for nested series)
    parent_id = Column(Integer, ForeignKey('series.id', ondelete='SET NULL'))
    sort_order = Column(Integer, default=0)  # Order within parent
    
    # Completion tracking
    target_count = Column(Integer)  # Expected number of items (NULL = open-ended)
    is_complete = Column(Boolean, default=False)
    completion_date = Column(DateTime)
    
    # Smart series criteria (JSON filter definition)
    smart_criteria = Column(JSON)  # {"ruler_id": [1,2,3], "metal": "silver", ...}
    auto_update = Column(Boolean, default=False)  # Auto-add matching coins
    
    # Display settings
    display_mode = Column(String(20), default="grid")  # grid, list, timeline, map
    cover_image_url = Column(String(500))
    color_theme = Column(String(20))  # For UI theming
    
    # Metadata
    is_template = Column(Boolean, default=False)  # Can be cloned by users
    is_canonical = Column(Boolean, default=False)  # Standard numismatic series
    is_public = Column(Boolean, default=False)  # Visible to others (future)
    is_active = Column(Boolean, default=True)
    is_archived = Column(Boolean, default=False)
    
    # Source (for canonical series)
    source_reference = Column(String(200))  # "Suetonius, De Vita Caesarum"
    nomisma_uri = Column(String(200))
    
    # Budget tracking
    budget_total = Column(Float)  # Total budget for series
    budget_spent = Column(Float, default=0)  # Calculated from owned coins
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    parent = relationship('Series', remote_side=[id], backref='children')
    slots = relationship('SeriesSlot', back_populates='series', cascade='all, delete-orphan')
    memberships = relationship('SeriesMembership', back_populates='series', cascade='all, delete-orphan')
    
    @property
    def filled_count(self) -> int:
        """Count of filled slots."""
        return sum(1 for s in self.slots if s.status == SlotStatus.FILLED)
    
    @property
    def completion_percentage(self) -> float:
        """Completion percentage."""
        if not self.target_count:
            return 0.0
        return (self.filled_count / self.target_count) * 100


class SeriesSlot(Base):
    """
    A defined position/slot within a series.
    
    For structured series (Twelve Caesars), each slot represents
    a specific required item. For open series, slots are created
    as coins are added.
    """
    __tablename__ = "series_slots"
    __table_args__ = (
        UniqueConstraint('series_id', 'slot_number', name='uq_series_slot_number'),
        UniqueConstraint('series_id', 'slug', name='uq_series_slot_slug'),
        Index('ix_series_slots_status', 'status'),
    )
    
    id = Column(Integer, primary_key=True)
    series_id = Column(Integer, ForeignKey('series.id', ondelete='CASCADE'), nullable=False)
    
    # Position
    slot_number = Column(Integer, nullable=False)  # 1-based position
    slug = Column(String(50))  # e.g., "augustus", "tiberius"
    
    # Definition (what should fill this slot)
    name = Column(String(200), nullable=False)  # "Augustus"
    description = Column(Text)  # "First Roman Emperor, 27 BC - 14 AD"
    
    # Criteria for matching (optional - for suggestions)
    match_criteria = Column(JSON)  # {"ruler_id": 1} or {"reference": "RIC I 207"}
    
    # Linked vocabulary (optional)
    issuer_id = Column(Integer, ForeignKey('issuers.id'))
    mint_id = Column(Integer, ForeignKey('mints.id'))
    denomination_id = Column(Integer, ForeignKey('denominations.id'))
    reference_normalized = Column(String(100))  # "ric.1.207"
    
    # Status
    status = Column(Enum(SlotStatus), default=SlotStatus.EMPTY)
    priority = Column(Integer, default=5)  # 1-10, for acquisition priority
    
    # Quality targets
    min_grade = Column(String(20))  # Minimum acceptable grade
    target_grade = Column(String(20))  # Ideal grade
    max_price = Column(Float)  # Budget cap for this slot
    
    # Display
    placeholder_image = Column(String(500))  # Image to show when empty
    sort_order = Column(Integer)  # Custom sort (if different from slot_number)
    
    # Metadata
    notes = Column(Text)  # Personal notes about this slot
    difficulty = Column(Integer)  # 1-10, how hard to find
    rarity_estimate = Column(String(20))  # "common", "scarce", "rare", "very_rare"
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    filled_at = Column(DateTime)  # When first filled
    
    # Relationships
    series = relationship('Series', back_populates='slots')
    issuer = relationship('Issuer')
    mint = relationship('Mint')
    denomination = relationship('Denomination')
    coins = relationship('SeriesMembership', back_populates='slot')


class SeriesMembership(Base):
    """
    Links a coin to a series (and optionally a specific slot).
    
    A coin can belong to multiple series.
    A slot can have multiple coins (for collectors wanting duplicates).
    """
    __tablename__ = "series_memberships"
    __table_args__ = (
        Index('ix_series_memberships_coin', 'coin_id'),
        Index('ix_series_memberships_series', 'series_id'),
    )
    
    id = Column(Integer, primary_key=True)
    series_id = Column(Integer, ForeignKey('series.id', ondelete='CASCADE'), nullable=False)
    coin_id = Column(Integer, ForeignKey('coins.id', ondelete='CASCADE'), nullable=False)
    slot_id = Column(Integer, ForeignKey('series_slots.id', ondelete='SET NULL'))
    
    # Assignment metadata
    is_primary = Column(Boolean, default=True)  # Primary coin for this slot
    assignment_method = Column(String(20))  # "manual", "auto", "suggested"
    assigned_at = Column(DateTime, default=datetime.utcnow)
    assigned_by = Column(String(100))
    
    # Quality assessment for this series context
    meets_criteria = Column(Boolean, default=True)
    upgrade_wanted = Column(Boolean, default=False)
    quality_notes = Column(Text)
    
    # Relationships
    series = relationship('Series', back_populates='memberships')
    coin = relationship('Coin', backref='series_memberships')
    slot = relationship('SeriesSlot', back_populates='coins')


class SeriesTemplate(Base):
    """
    Predefined series templates that users can instantiate.
    
    Contains canonical series definitions (Twelve Caesars)
    and community-contributed templates.
    """
    __tablename__ = "series_templates"
    
    id = Column(Integer, primary_key=True)
    
    # Identity
    name = Column(String(200), nullable=False)
    slug = Column(String(100), unique=True, index=True)
    description = Column(Text)
    
    # Classification
    series_type = Column(Enum(SeriesType), nullable=False)
    category = Column(String(50))
    difficulty = Column(Integer)  # 1-10 overall difficulty
    
    # Template data (JSON blob with full series definition)
    template_data = Column(JSON, nullable=False)
    # Structure:
    # {
    #   "slots": [
    #     {"number": 1, "name": "Julius Caesar", "issuer_nomisma": "julius_caesar", ...},
    #     {"number": 2, "name": "Augustus", ...},
    #   ],
    #   "settings": {"display_mode": "grid", ...},
    #   "metadata": {"source": "Suetonius", ...}
    # }
    
    # Stats
    slot_count = Column(Integer)
    estimated_cost_low = Column(Float)  # Budget estimate (low end)
    estimated_cost_high = Column(Float)  # Budget estimate (high end)
    times_used = Column(Integer, default=0)  # Popularity tracking
    
    # Source
    source_reference = Column(String(200))
    author = Column(String(100))  # Template creator
    
    # Status
    is_canonical = Column(Boolean, default=False)  # Official/standard
    is_verified = Column(Boolean, default=False)  # Reviewed for accuracy
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)


class WishlistItem(Base):
    """
    Items wanted for collection, often linked to series gaps.
    """
    __tablename__ = "wishlist_items"
    __table_args__ = (
        Index('ix_wishlist_priority', 'priority'),
        Index('ix_wishlist_active', 'is_active'),
    )
    
    id = Column(Integer, primary_key=True)
    
    # What is wanted
    description = Column(String(500), nullable=False)  # "Augustus denarius, Lugdunum"
    
    # Linked to series (optional)
    series_id = Column(Integer, ForeignKey('series.id', ondelete='SET NULL'))
    slot_id = Column(Integer, ForeignKey('series_slots.id', ondelete='SET NULL'))
    
    # Criteria for matching
    match_criteria = Column(JSON)
    # {
    #   "ruler_id": 1,
    #   "mint_id": 5,
    #   "reference_pattern": "ric.1.*",
    #   "min_grade": "VF",
    #   "max_price": 500
    # }
    
    # Linked vocabulary
    issuer_id = Column(Integer, ForeignKey('issuers.id'))
    mint_id = Column(Integer, ForeignKey('mints.id'))
    denomination_id = Column(Integer, ForeignKey('denominations.id'))
    reference_normalized = Column(String(100))
    
    # Priority and budget
    priority = Column(Integer, default=5)  # 1-10
    max_price = Column(Float)
    target_price = Column(Float)  # Ideal price point
    
    # Quality requirements
    min_grade = Column(String(20))
    preferred_grade = Column(String(20))
    
    # Status
    is_active = Column(Boolean, default=True)
    is_fulfilled = Column(Boolean, default=False)
    fulfilled_by_coin_id = Column(Integer, ForeignKey('coins.id', ondelete='SET NULL'))
    fulfilled_at = Column(DateTime)
    
    # Alerts
    alert_enabled = Column(Boolean, default=False)
    alert_sources = Column(JSON)  # ["heritage", "cng", "vcoins"]
    last_alert_at = Column(DateTime)
    
    # Notes
    notes = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    # Relationships
    series = relationship('Series')
    slot = relationship('SeriesSlot')
    issuer = relationship('Issuer')
    fulfilled_by = relationship('Coin')
```

---

## Canonical Series Templates

### The Twelve Caesars

```python
TWELVE_CAESARS_TEMPLATE = {
    "name": "The Twelve Caesars",
    "slug": "twelve-caesars",
    "description": "The twelve rulers of Rome from Julius Caesar to Domitian, as chronicled by Suetonius in De Vita Caesarum (c. 121 AD).",
    "series_type": "canonical",
    "category": "imperial",
    "source_reference": "Suetonius, De Vita Caesarum",
    "slots": [
        {
            "number": 1,
            "name": "Julius Caesar",
            "slug": "julius-caesar",
            "description": "Dictator 49-44 BC. Assassinated on the Ides of March.",
            "issuer_nomisma": "julius_caesar",
            "date_range": [-49, -44],
            "difficulty": 6,
            "rarity": "scarce",
            "typical_denominations": ["denarius", "aureus"],
            "reference_pattern": "crawford.4*",
            "price_estimate": {"low": 300, "mid": 800, "high": 5000},
        },
        {
            "number": 2,
            "name": "Augustus",
            "slug": "augustus",
            "description": "First Emperor 27 BC - 14 AD. Founded the Principate.",
            "issuer_nomisma": "augustus",
            "date_range": [-27, 14],
            "difficulty": 3,
            "rarity": "common",
            "typical_denominations": ["denarius", "aureus", "as"],
            "reference_pattern": "ric.1.*",
            "price_estimate": {"low": 150, "mid": 400, "high": 3000},
        },
        {
            "number": 3,
            "name": "Tiberius",
            "slug": "tiberius",
            "description": "Emperor 14-37 AD. 'Tribute Penny' of the Bible.",
            "issuer_nomisma": "tiberius",
            "date_range": [14, 37],
            "difficulty": 4,
            "rarity": "common",
            "typical_denominations": ["denarius", "as", "sestertius"],
            "reference_pattern": "ric.1.*",
            "price_estimate": {"low": 200, "mid": 500, "high": 2000},
            "notes": "The 'Tribute Penny' (RIC 30) is especially popular.",
        },
        {
            "number": 4,
            "name": "Caligula",
            "slug": "caligula",
            "description": "Emperor 37-41 AD. Notorious for cruelty and excess.",
            "issuer_nomisma": "caligula",
            "date_range": [37, 41],
            "difficulty": 7,
            "rarity": "scarce",
            "typical_denominations": ["as", "sestertius"],
            "reference_pattern": "ric.1.*",
            "price_estimate": {"low": 400, "mid": 1500, "high": 10000},
            "notes": "Silver is rare. Bronze more available.",
        },
        {
            "number": 5,
            "name": "Claudius",
            "slug": "claudius",
            "description": "Emperor 41-54 AD. Conquered Britain.",
            "issuer_nomisma": "claudius",
            "date_range": [41, 54],
            "difficulty": 5,
            "rarity": "common",
            "typical_denominations": ["as", "sestertius", "denarius"],
            "reference_pattern": "ric.1.*",
            "price_estimate": {"low": 100, "mid": 350, "high": 2500},
        },
        {
            "number": 6,
            "name": "Nero",
            "slug": "nero",
            "description": "Emperor 54-68 AD. Last of the Julio-Claudians.",
            "issuer_nomisma": "nero",
            "date_range": [54, 68],
            "difficulty": 4,
            "rarity": "common",
            "typical_denominations": ["denarius", "sestertius", "as"],
            "reference_pattern": "ric.1.*",
            "price_estimate": {"low": 150, "mid": 500, "high": 4000},
        },
        {
            "number": 7,
            "name": "Galba",
            "slug": "galba",
            "description": "Emperor Jun 68 - Jan 69 AD. First of the 'Year of Four Emperors'.",
            "issuer_nomisma": "galba",
            "date_range": [68, 69],
            "difficulty": 7,
            "rarity": "scarce",
            "typical_denominations": ["denarius", "sestertius"],
            "reference_pattern": "ric.1.*",
            "price_estimate": {"low": 300, "mid": 800, "high": 5000},
        },
        {
            "number": 8,
            "name": "Otho",
            "slug": "otho",
            "description": "Emperor Jan-Apr 69 AD. Reigned only 3 months.",
            "issuer_nomisma": "otho",
            "date_range": [69, 69],
            "difficulty": 9,
            "rarity": "rare",
            "typical_denominations": ["denarius"],
            "reference_pattern": "ric.1.*",
            "price_estimate": {"low": 1500, "mid": 4000, "high": 15000},
            "notes": "Scarce due to short reign. Key coin for the set.",
        },
        {
            "number": 9,
            "name": "Vitellius",
            "slug": "vitellius",
            "description": "Emperor Apr-Dec 69 AD. Reigned 8 months.",
            "issuer_nomisma": "vitellius",
            "date_range": [69, 69],
            "difficulty": 8,
            "rarity": "scarce",
            "typical_denominations": ["denarius", "sestertius"],
            "reference_pattern": "ric.1.*",
            "price_estimate": {"low": 600, "mid": 1500, "high": 8000},
        },
        {
            "number": 10,
            "name": "Vespasian",
            "slug": "vespasian",
            "description": "Emperor 69-79 AD. Founded the Flavian dynasty.",
            "issuer_nomisma": "vespasian",
            "date_range": [69, 79],
            "difficulty": 2,
            "rarity": "common",
            "typical_denominations": ["denarius", "sestertius", "as"],
            "reference_pattern": "ric.2.*",
            "price_estimate": {"low": 80, "mid": 200, "high": 1500},
        },
        {
            "number": 11,
            "name": "Titus",
            "slug": "titus",
            "description": "Emperor 79-81 AD. Destroyed Jerusalem. Completed Colosseum.",
            "issuer_nomisma": "titus",
            "date_range": [79, 81],
            "difficulty": 5,
            "rarity": "common",
            "typical_denominations": ["denarius", "sestertius"],
            "reference_pattern": "ric.2.*",
            "price_estimate": {"low": 150, "mid": 400, "high": 3000},
        },
        {
            "number": 12,
            "name": "Domitian",
            "slug": "domitian",
            "description": "Emperor 81-96 AD. Last of the Flavians.",
            "issuer_nomisma": "domitian",
            "date_range": [81, 96],
            "difficulty": 2,
            "rarity": "common",
            "typical_denominations": ["denarius", "sestertius", "as"],
            "reference_pattern": "ric.2.*",
            "price_estimate": {"low": 60, "mid": 150, "high": 1000},
        },
    ],
    "settings": {
        "display_mode": "grid",
        "sort_by": "slot_number",
    },
    "metadata": {
        "total_estimated_cost": {"low": 4090, "mid": 10800, "high": 59000},
        "key_coins": ["otho", "vitellius", "galba"],
        "entry_point": ["vespasian", "domitian"],  # Easiest to start
        "bibliography": [
            "Suetonius, De Vita Caesarum",
            "RIC I (2nd ed.)",
            "RIC II",
        ],
    },
}
```

### Five Good Emperors

```python
FIVE_GOOD_EMPERORS_TEMPLATE = {
    "name": "The Five Good Emperors",
    "slug": "five-good-emperors",
    "description": "The period of the 'Pax Romana' under Nerva, Trajan, Hadrian, Antoninus Pius, and Marcus Aurelius (96-180 AD).",
    "series_type": "canonical",
    "category": "imperial",
    "source_reference": "Edward Gibbon, Decline and Fall of the Roman Empire",
    "slots": [
        {
            "number": 1,
            "name": "Nerva",
            "slug": "nerva",
            "description": "Emperor 96-98 AD. First of the Adoptive Emperors.",
            "issuer_nomisma": "nerva",
            "date_range": [96, 98],
            "difficulty": 5,
            "rarity": "common",
            "price_estimate": {"low": 100, "mid": 300, "high": 2000},
        },
        {
            "number": 2,
            "name": "Trajan",
            "slug": "trajan",
            "description": "Emperor 98-117 AD. Empire at greatest extent.",
            "issuer_nomisma": "trajan",
            "date_range": [98, 117],
            "difficulty": 2,
            "rarity": "common",
            "price_estimate": {"low": 50, "mid": 150, "high": 1000},
        },
        {
            "number": 3,
            "name": "Hadrian",
            "slug": "hadrian",
            "description": "Emperor 117-138 AD. Built Hadrian's Wall.",
            "issuer_nomisma": "hadrian",
            "date_range": [117, 138],
            "difficulty": 2,
            "rarity": "common",
            "price_estimate": {"low": 50, "mid": 150, "high": 1500},
        },
        {
            "number": 4,
            "name": "Antoninus Pius",
            "slug": "antoninus-pius",
            "description": "Emperor 138-161 AD. Peaceful reign.",
            "issuer_nomisma": "antoninus_pius",
            "date_range": [138, 161],
            "difficulty": 2,
            "rarity": "common",
            "price_estimate": {"low": 40, "mid": 120, "high": 800},
        },
        {
            "number": 5,
            "name": "Marcus Aurelius",
            "slug": "marcus-aurelius",
            "description": "Emperor 161-180 AD. Philosopher Emperor.",
            "issuer_nomisma": "marcus_aurelius",
            "date_range": [161, 180],
            "difficulty": 2,
            "rarity": "common",
            "price_estimate": {"low": 40, "mid": 120, "high": 800},
        },
    ],
    "settings": {
        "display_mode": "grid",
    },
    "metadata": {
        "total_estimated_cost": {"low": 280, "mid": 840, "high": 6100},
        "notes": "Excellent starter series. All rulers are readily available.",
    },
}
```

### Additional Templates to Include

```python
SERIES_TEMPLATES = [
    # Imperial
    "twelve-caesars",
    "five-good-emperors",
    "severan-dynasty",
    "year-of-four-emperors",
    "year-of-five-emperors",
    "year-of-six-emperors",
    "gallic-emperors",
    "britannic-emperors",
    "tetrarchy",
    "constantinian-dynasty",
    "valentinian-dynasty",
    "theodosian-dynasty",
    
    # Republican
    "roman-republic-moneyers",
    "imperators-civil-war",
    "triumvirs",
    
    # Thematic
    "judaea-capta",
    "parthian-victories",
    "legionary-denarii-antony",
    "travel-series-hadrian",
    "consecratio-series",
    "divi-series",
    "animals-on-roman-coins",
    "architectural-reverses",
    "zodiac-alexandrian",
    
    # Geographic
    "alexandria-tetradrachms",
    "antioch-mint",
    "eastern-mints-augustus",
    
    # Metal-based
    "roman-gold-aurei",
    "republican-denarii",
    "late-roman-bronze",
]
```

---

## Services

### Series Service

```python
# services/series_service.py
"""
Series management service.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_
from datetime import datetime
from typing import Optional
import structlog

from app.models.series import (
    Series, SeriesSlot, SeriesMembership, SeriesTemplate,
    WishlistItem, SeriesType, SlotStatus
)
from app.models.coin import Coin

logger = structlog.get_logger()


class SeriesService:
    """
    Manages coin series creation, membership, and tracking.
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    # === Series CRUD ===
    
    def create_series(
        self,
        name: str,
        series_type: SeriesType = SeriesType.USER_DEFINED,
        description: str | None = None,
        parent_id: int | None = None,
        **kwargs,
    ) -> Series:
        """Create a new series."""
        # Generate slug
        slug = self._generate_slug(name)
        
        series = Series(
            name=name,
            slug=slug,
            series_type=series_type,
            description=description,
            parent_id=parent_id,
            **kwargs,
        )
        self.db.add(series)
        self.db.commit()
        self.db.refresh(series)
        
        logger.info("series_created", series_id=series.id, name=name, type=series_type.value)
        return series
    
    def create_from_template(
        self,
        template_id: int,
        customizations: dict | None = None,
    ) -> Series:
        """
        Create a series from a template.
        
        Args:
            template_id: Template to instantiate
            customizations: Optional overrides (name, slots to include, etc.)
        """
        template = self.db.query(SeriesTemplate).get(template_id)
        if not template:
            raise ValueError(f"Template {template_id} not found")
        
        # Extract template data
        data = template.template_data
        customs = customizations or {}
        
        # Create series
        series = self.create_series(
            name=customs.get("name", template.name),
            series_type=template.series_type,
            description=customs.get("description", template.description),
            category=template.category,
            target_count=template.slot_count,
            source_reference=template.source_reference,
            is_canonical=template.is_canonical,
        )
        
        # Create slots
        included_slugs = customs.get("include_slots")  # None = all
        for slot_data in data.get("slots", []):
            if included_slugs and slot_data["slug"] not in included_slugs:
                continue
            
            slot = SeriesSlot(
                series_id=series.id,
                slot_number=slot_data["number"],
                slug=slot_data.get("slug"),
                name=slot_data["name"],
                description=slot_data.get("description"),
                difficulty=slot_data.get("difficulty"),
                rarity_estimate=slot_data.get("rarity"),
                match_criteria={
                    "issuer_nomisma": slot_data.get("issuer_nomisma"),
                    "reference_pattern": slot_data.get("reference_pattern"),
                },
            )
            self.db.add(slot)
        
        # Update template usage count
        template.times_used += 1
        
        self.db.commit()
        self.db.refresh(series)
        
        logger.info(
            "series_created_from_template",
            series_id=series.id,
            template_id=template_id,
            slots_created=len(series.slots),
        )
        
        return series
    
    def create_smart_series(
        self,
        name: str,
        criteria: dict,
        auto_update: bool = True,
    ) -> Series:
        """
        Create a smart/dynamic series based on filter criteria.
        
        Args:
            name: Series name
            criteria: Filter criteria (same format as coin search)
            auto_update: Whether to auto-add matching coins
        """
        series = self.create_series(
            name=name,
            series_type=SeriesType.SMART,
            smart_criteria=criteria,
            auto_update=auto_update,
        )
        
        # Initial population
        if auto_update:
            self.refresh_smart_series(series.id)
        
        return series
    
    # === Membership Management ===
    
    def add_coin_to_series(
        self,
        series_id: int,
        coin_id: int,
        slot_id: int | None = None,
        is_primary: bool = True,
    ) -> SeriesMembership:
        """
        Add a coin to a series.
        
        Args:
            series_id: Target series
            coin_id: Coin to add
            slot_id: Specific slot (optional)
            is_primary: Whether this is the primary coin for the slot
        """
        # Validate
        series = self.db.query(Series).get(series_id)
        if not series:
            raise ValueError(f"Series {series_id} not found")
        
        coin = self.db.query(Coin).get(coin_id)
        if not coin:
            raise ValueError(f"Coin {coin_id} not found")
        
        # Check for existing membership
        existing = self.db.query(SeriesMembership).filter(
            SeriesMembership.series_id == series_id,
            SeriesMembership.coin_id == coin_id,
        ).first()
        
        if existing:
            if slot_id and existing.slot_id != slot_id:
                existing.slot_id = slot_id
                self.db.commit()
            return existing
        
        # Create membership
        membership = SeriesMembership(
            series_id=series_id,
            coin_id=coin_id,
            slot_id=slot_id,
            is_primary=is_primary,
            assignment_method="manual",
        )
        self.db.add(membership)
        
        # Update slot status
        if slot_id:
            slot = self.db.query(SeriesSlot).get(slot_id)
            if slot:
                slot.status = SlotStatus.FILLED
                slot.filled_at = datetime.utcnow()
        
        # Update series completion
        self._update_series_completion(series)
        
        self.db.commit()
        self.db.refresh(membership)
        
        logger.info(
            "coin_added_to_series",
            series_id=series_id,
            coin_id=coin_id,
            slot_id=slot_id,
        )
        
        return membership
    
    def remove_coin_from_series(
        self,
        series_id: int,
        coin_id: int,
    ) -> bool:
        """Remove a coin from a series."""
        membership = self.db.query(SeriesMembership).filter(
            SeriesMembership.series_id == series_id,
            SeriesMembership.coin_id == coin_id,
        ).first()
        
        if not membership:
            return False
        
        # Update slot status
        if membership.slot_id:
            slot = self.db.query(SeriesSlot).get(membership.slot_id)
            if slot:
                # Check if other coins fill this slot
                other_coins = self.db.query(SeriesMembership).filter(
                    SeriesMembership.slot_id == membership.slot_id,
                    SeriesMembership.id != membership.id,
                ).count()
                
                if other_coins == 0:
                    slot.status = SlotStatus.EMPTY
                    slot.filled_at = None
        
        self.db.delete(membership)
        
        # Update series completion
        series = self.db.query(Series).get(series_id)
        self._update_series_completion(series)
        
        self.db.commit()
        return True
    
    def suggest_slot_for_coin(
        self,
        series_id: int,
        coin_id: int,
    ) -> SeriesSlot | None:
        """
        Suggest the best slot for a coin in a series.
        
        Uses match_criteria on slots to find best fit.
        """
        series = self.db.query(Series).get(series_id)
        coin = self.db.query(Coin).get(coin_id)
        
        if not series or not coin:
            return None
        
        best_slot = None
        best_score = 0
        
        for slot in series.slots:
            if slot.status == SlotStatus.FILLED:
                continue
            
            score = self._calculate_slot_match_score(slot, coin)
            if score > best_score:
                best_score = score
                best_slot = slot
        
        return best_slot if best_score > 0.5 else None
    
    def _calculate_slot_match_score(self, slot: SeriesSlot, coin: Coin) -> float:
        """Calculate how well a coin matches a slot's criteria."""
        if not slot.match_criteria:
            return 0.0
        
        criteria = slot.match_criteria
        score = 0.0
        checks = 0
        
        # Check issuer
        if "issuer_id" in criteria and coin.ruler_id:
            checks += 1
            if coin.ruler_id == criteria["issuer_id"]:
                score += 1.0
        
        if "issuer_nomisma" in criteria and coin.ruler:
            checks += 1
            # Would need to look up issuer's nomisma_id
            # Simplified here
            if criteria["issuer_nomisma"].lower() in coin.ruler.canonical_name.lower():
                score += 0.8
        
        # Check reference pattern
        if "reference_pattern" in criteria:
            checks += 1
            pattern = criteria["reference_pattern"]
            for ref in coin.references:
                if self._reference_matches_pattern(ref.normalized_key, pattern):
                    score += 1.0
                    break
        
        return score / checks if checks > 0 else 0.0
    
    def _reference_matches_pattern(self, ref: str, pattern: str) -> bool:
        """Check if reference matches pattern (supports * wildcard)."""
        import fnmatch
        return fnmatch.fnmatch(ref, pattern)
    
    # === Smart Series ===
    
    def refresh_smart_series(self, series_id: int) -> int:
        """
        Refresh a smart series by re-evaluating criteria.
        
        Returns:
            Number of coins added/removed
        """
        series = self.db.query(Series).get(series_id)
        if not series or series.series_type != SeriesType.SMART:
            return 0
        
        if not series.smart_criteria:
            return 0
        
        # Find matching coins
        matching_coins = self._find_coins_matching_criteria(series.smart_criteria)
        matching_ids = {c.id for c in matching_coins}
        
        # Get current members
        current_members = self.db.query(SeriesMembership.coin_id).filter(
            SeriesMembership.series_id == series_id
        ).all()
        current_ids = {m[0] for m in current_members}
        
        # Add new matches
        added = 0
        for coin_id in matching_ids - current_ids:
            membership = SeriesMembership(
                series_id=series_id,
                coin_id=coin_id,
                assignment_method="auto",
            )
            self.db.add(membership)
            added += 1
        
        # Remove non-matches (only if auto-assigned)
        removed = 0
        for coin_id in current_ids - matching_ids:
            self.db.query(SeriesMembership).filter(
                SeriesMembership.series_id == series_id,
                SeriesMembership.coin_id == coin_id,
                SeriesMembership.assignment_method == "auto",
            ).delete()
            removed += 1
        
        self.db.commit()
        
        logger.info(
            "smart_series_refreshed",
            series_id=series_id,
            added=added,
            removed=removed,
        )
        
        return added + removed
    
    def _find_coins_matching_criteria(self, criteria: dict) -> list[Coin]:
        """Find coins matching smart series criteria."""
        query = self.db.query(Coin)
        
        if "ruler_id" in criteria:
            if isinstance(criteria["ruler_id"], list):
                query = query.filter(Coin.ruler_id.in_(criteria["ruler_id"]))
            else:
                query = query.filter(Coin.ruler_id == criteria["ruler_id"])
        
        if "mint_id" in criteria:
            query = query.filter(Coin.mint_id == criteria["mint_id"])
        
        if "metal" in criteria:
            query = query.filter(Coin.metal == criteria["metal"])
        
        if "denomination" in criteria:
            query = query.filter(Coin.denomination.ilike(f"%{criteria['denomination']}%"))
        
        if "category" in criteria:
            query = query.filter(Coin.category == criteria["category"])
        
        if "min_weight" in criteria:
            query = query.filter(Coin.weight_g >= criteria["min_weight"])
        
        if "max_weight" in criteria:
            query = query.filter(Coin.weight_g <= criteria["max_weight"])
        
        if "date_from" in criteria:
            query = query.filter(Coin.date_start >= criteria["date_from"])
        
        if "date_to" in criteria:
            query = query.filter(Coin.date_end <= criteria["date_to"])
        
        return query.all()
    
    # === Completion & Analytics ===
    
    def get_series_stats(self, series_id: int) -> dict:
        """Get comprehensive statistics for a series."""
        series = self.db.query(Series).get(series_id)
        if not series:
            return {}
        
        slots = series.slots
        memberships = series.memberships
        
        # Slot status breakdown
        status_counts = {}
        for status in SlotStatus:
            status_counts[status.value] = sum(1 for s in slots if s.status == status)
        
        # Value calculations
        total_value = sum(
            m.coin.current_value or 0
            for m in memberships
            if m.coin and m.coin.current_value
        )
        
        total_cost = sum(
            m.coin.purchase_price or 0
            for m in memberships
            if m.coin and m.coin.purchase_price
        )
        
        # Gap analysis
        gaps = [s for s in slots if s.status in (SlotStatus.EMPTY, SlotStatus.WANTED)]
        gap_difficulties = [s.difficulty for s in gaps if s.difficulty]
        
        return {
            "series_id": series_id,
            "name": series.name,
            "type": series.series_type.value,
            "completion": {
                "target": series.target_count,
                "filled": status_counts.get(SlotStatus.FILLED.value, 0),
                "percentage": series.completion_percentage,
                "is_complete": series.is_complete,
            },
            "slots": {
                "total": len(slots),
                "by_status": status_counts,
            },
            "members": {
                "total": len(memberships),
                "unique_coins": len(set(m.coin_id for m in memberships)),
            },
            "value": {
                "total_value": total_value,
                "total_cost": total_cost,
                "gain_loss": total_value - total_cost,
            },
            "gaps": {
                "count": len(gaps),
                "avg_difficulty": sum(gap_difficulties) / len(gap_difficulties) if gap_difficulties else None,
                "items": [
                    {
                        "slot_id": s.id,
                        "name": s.name,
                        "difficulty": s.difficulty,
                        "rarity": s.rarity_estimate,
                    }
                    for s in gaps[:10]
                ],
            },
            "budget": {
                "total": series.budget_total,
                "spent": series.budget_spent,
                "remaining": (series.budget_total - series.budget_spent) if series.budget_total else None,
            },
        }
    
    def get_gap_analysis(self, series_id: int) -> list[dict]:
        """
        Get detailed gap analysis for a series.
        
        Returns list of missing items with acquisition suggestions.
        """
        series = self.db.query(Series).get(series_id)
        if not series:
            return []
        
        gaps = []
        for slot in series.slots:
            if slot.status not in (SlotStatus.EMPTY, SlotStatus.WANTED):
                continue
            
            gap = {
                "slot_id": slot.id,
                "slot_number": slot.slot_number,
                "name": slot.name,
                "description": slot.description,
                "difficulty": slot.difficulty,
                "rarity": slot.rarity_estimate,
                "max_price": slot.max_price,
                "priority": slot.priority,
                "match_criteria": slot.match_criteria,
                "suggestions": [],
            }
            
            # Find potential matches in collection that aren't assigned
            # (coins that could fill this slot)
            # ... implementation would query coins matching criteria
            
            gaps.append(gap)
        
        # Sort by priority then difficulty
        gaps.sort(key=lambda g: (g["priority"] or 5, g["difficulty"] or 5))
        
        return gaps
    
    def _update_series_completion(self, series: Series):
        """Update series completion status."""
        if not series.target_count:
            return
        
        filled = sum(1 for s in series.slots if s.status == SlotStatus.FILLED)
        series.is_complete = filled >= series.target_count
        
        if series.is_complete and not series.completion_date:
            series.completion_date = datetime.utcnow()
            logger.info("series_completed", series_id=series.id, name=series.name)
    
    def _generate_slug(self, name: str) -> str:
        """Generate URL-friendly slug from name."""
        import re
        slug = name.lower()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_]+', '-', slug)
        slug = slug.strip('-')
        
        # Ensure uniqueness
        base_slug = slug
        counter = 1
        while self.db.query(Series).filter(Series.slug == slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1
        
        return slug
    
    # === Wishlist Integration ===
    
    def sync_gaps_to_wishlist(self, series_id: int) -> int:
        """
        Create wishlist items for series gaps.
        
        Returns number of wishlist items created.
        """
        series = self.db.query(Series).get(series_id)
        if not series:
            return 0
        
        created = 0
        for slot in series.slots:
            if slot.status not in (SlotStatus.WANTED, SlotStatus.EMPTY):
                continue
            
            # Check if wishlist item exists
            existing = self.db.query(WishlistItem).filter(
                WishlistItem.slot_id == slot.id,
                WishlistItem.is_active == True,
            ).first()
            
            if existing:
                continue
            
            # Create wishlist item
            item = WishlistItem(
                description=f"{slot.name} for {series.name}",
                series_id=series_id,
                slot_id=slot.id,
                issuer_id=slot.issuer_id,
                mint_id=slot.mint_id,
                denomination_id=slot.denomination_id,
                match_criteria=slot.match_criteria,
                priority=slot.priority or 5,
                max_price=slot.max_price,
                min_grade=slot.min_grade,
                preferred_grade=slot.target_grade,
            )
            self.db.add(item)
            created += 1
        
        self.db.commit()
        return created
```

---

## API Endpoints

```python
# routers/series.py
"""
Series management API endpoints.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional

from app.database import get_db
from app.models.series import Series, SeriesSlot, SeriesMembership, SeriesTemplate, SeriesType, SlotStatus
from app.services.series_service import SeriesService
from app.schemas.series import (
    SeriesCreate, SeriesUpdate, SeriesResponse, SeriesStatsResponse,
    SlotCreate, SlotUpdate, MembershipCreate, GapAnalysisResponse,
)

router = APIRouter(prefix="/api/series", tags=["series"])


# === Series CRUD ===

@router.get("")
def list_series(
    series_type: SeriesType | None = None,
    category: str | None = None,
    include_archived: bool = False,
    search: str | None = None,
    limit: int = Query(50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """List all series with filtering."""
    query = db.query(Series)
    
    if not include_archived:
        query = query.filter(Series.is_archived == False)
    
    if series_type:
        query = query.filter(Series.series_type == series_type)
    
    if category:
        query = query.filter(Series.category == category)
    
    if search:
        query = query.filter(Series.name.ilike(f"%{search}%"))
    
    total = query.count()
    items = query.order_by(Series.name).offset(offset).limit(limit).all()
    
    return {
        "items": [
            {
                "id": s.id,
                "name": s.name,
                "slug": s.slug,
                "type": s.series_type.value,
                "category": s.category,
                "target_count": s.target_count,
                "filled_count": s.filled_count,
                "completion_percentage": s.completion_percentage,
                "is_complete": s.is_complete,
            }
            for s in items
        ],
        "total": total,
    }


@router.post("")
def create_series(
    data: SeriesCreate,
    db: Session = Depends(get_db),
):
    """Create a new series."""
    service = SeriesService(db)
    
    if data.template_id:
        series = service.create_from_template(
            data.template_id,
            {"name": data.name, "description": data.description},
        )
    elif data.smart_criteria:
        series = service.create_smart_series(
            data.name,
            data.smart_criteria,
            data.auto_update or True,
        )
    else:
        series = service.create_series(
            name=data.name,
            series_type=data.series_type or SeriesType.USER_DEFINED,
            description=data.description,
            category=data.category,
            target_count=data.target_count,
        )
    
    return {"id": series.id, "slug": series.slug}


@router.get("/{series_id}")
def get_series(series_id: int, db: Session = Depends(get_db)):
    """Get series details including slots and members."""
    series = db.query(Series).filter(Series.id == series_id).first()
    if not series:
        raise HTTPException(404, "Series not found")
    
    return {
        "id": series.id,
        "name": series.name,
        "slug": series.slug,
        "description": series.description,
        "type": series.series_type.value,
        "category": series.category,
        "parent_id": series.parent_id,
        "target_count": series.target_count,
        "is_complete": series.is_complete,
        "completion_date": series.completion_date,
        "smart_criteria": series.smart_criteria,
        "budget": {
            "total": series.budget_total,
            "spent": series.budget_spent,
        },
        "slots": [
            {
                "id": s.id,
                "number": s.slot_number,
                "name": s.name,
                "status": s.status.value,
                "difficulty": s.difficulty,
                "rarity": s.rarity_estimate,
                "coins": [
                    {"id": m.coin_id, "is_primary": m.is_primary}
                    for m in s.coins
                ],
            }
            for s in sorted(series.slots, key=lambda x: x.slot_number)
        ],
        "stats": SeriesService(db).get_series_stats(series_id),
    }


@router.put("/{series_id}")
def update_series(
    series_id: int,
    data: SeriesUpdate,
    db: Session = Depends(get_db),
):
    """Update a series."""
    series = db.query(Series).filter(Series.id == series_id).first()
    if not series:
        raise HTTPException(404, "Series not found")
    
    for key, value in data.dict(exclude_unset=True).items():
        setattr(series, key, value)
    
    db.commit()
    return {"status": "updated"}


@router.delete("/{series_id}")
def delete_series(series_id: int, db: Session = Depends(get_db)):
    """Delete a series (or archive if has history)."""
    series = db.query(Series).filter(Series.id == series_id).first()
    if not series:
        raise HTTPException(404, "Series not found")
    
    # Archive if has members, delete if empty
    if series.memberships:
        series.is_archived = True
        series.is_active = False
    else:
        db.delete(series)
    
    db.commit()
    return {"status": "deleted" if not series.memberships else "archived"}


# === Slots ===

@router.post("/{series_id}/slots")
def add_slot(
    series_id: int,
    data: SlotCreate,
    db: Session = Depends(get_db),
):
    """Add a slot to a series."""
    series = db.query(Series).filter(Series.id == series_id).first()
    if not series:
        raise HTTPException(404, "Series not found")
    
    # Get next slot number
    max_slot = db.query(func.max(SeriesSlot.slot_number)).filter(
        SeriesSlot.series_id == series_id
    ).scalar() or 0
    
    slot = SeriesSlot(
        series_id=series_id,
        slot_number=data.slot_number or (max_slot + 1),
        name=data.name,
        description=data.description,
        match_criteria=data.match_criteria,
        difficulty=data.difficulty,
        rarity_estimate=data.rarity_estimate,
        max_price=data.max_price,
    )
    db.add(slot)
    
    # Update target count
    if series.target_count:
        series.target_count += 1
    
    db.commit()
    return {"id": slot.id}


@router.put("/{series_id}/slots/{slot_id}")
def update_slot(
    series_id: int,
    slot_id: int,
    data: SlotUpdate,
    db: Session = Depends(get_db),
):
    """Update a slot."""
    slot = db.query(SeriesSlot).filter(
        SeriesSlot.id == slot_id,
        SeriesSlot.series_id == series_id,
    ).first()
    
    if not slot:
        raise HTTPException(404, "Slot not found")
    
    for key, value in data.dict(exclude_unset=True).items():
        setattr(slot, key, value)
    
    db.commit()
    return {"status": "updated"}


# === Membership ===

@router.post("/{series_id}/coins/{coin_id}")
def add_coin_to_series(
    series_id: int,
    coin_id: int,
    slot_id: int | None = None,
    db: Session = Depends(get_db),
):
    """Add a coin to a series."""
    service = SeriesService(db)
    
    # Auto-suggest slot if not provided
    if not slot_id:
        suggested = service.suggest_slot_for_coin(series_id, coin_id)
        if suggested:
            slot_id = suggested.id
    
    membership = service.add_coin_to_series(series_id, coin_id, slot_id)
    return {
        "membership_id": membership.id,
        "slot_id": membership.slot_id,
        "suggested": slot_id is None,
    }


@router.delete("/{series_id}/coins/{coin_id}")
def remove_coin_from_series(
    series_id: int,
    coin_id: int,
    db: Session = Depends(get_db),
):
    """Remove a coin from a series."""
    service = SeriesService(db)
    removed = service.remove_coin_from_series(series_id, coin_id)
    
    if not removed:
        raise HTTPException(404, "Membership not found")
    
    return {"status": "removed"}


@router.post("/{series_id}/coins/{coin_id}/move")
def move_coin_to_slot(
    series_id: int,
    coin_id: int,
    slot_id: int,
    db: Session = Depends(get_db),
):
    """Move a coin to a different slot within a series."""
    membership = db.query(SeriesMembership).filter(
        SeriesMembership.series_id == series_id,
        SeriesMembership.coin_id == coin_id,
    ).first()
    
    if not membership:
        raise HTTPException(404, "Membership not found")
    
    # Update old slot status
    if membership.slot_id:
        old_slot = db.query(SeriesSlot).get(membership.slot_id)
        if old_slot:
            # Check if other coins still fill this slot
            other = db.query(SeriesMembership).filter(
                SeriesMembership.slot_id == membership.slot_id,
                SeriesMembership.id != membership.id,
            ).count()
            if other == 0:
                old_slot.status = SlotStatus.EMPTY
    
    # Update to new slot
    membership.slot_id = slot_id
    new_slot = db.query(SeriesSlot).get(slot_id)
    if new_slot:
        new_slot.status = SlotStatus.FILLED
        new_slot.filled_at = datetime.utcnow()
    
    db.commit()
    return {"status": "moved"}


# === Analytics ===

@router.get("/{series_id}/stats")
def get_series_stats(series_id: int, db: Session = Depends(get_db)):
    """Get comprehensive series statistics."""
    service = SeriesService(db)
    return service.get_series_stats(series_id)


@router.get("/{series_id}/gaps")
def get_gap_analysis(series_id: int, db: Session = Depends(get_db)):
    """Get gap analysis with acquisition suggestions."""
    service = SeriesService(db)
    return service.get_gap_analysis(series_id)


@router.post("/{series_id}/sync-wishlist")
def sync_to_wishlist(series_id: int, db: Session = Depends(get_db)):
    """Create wishlist items from series gaps."""
    service = SeriesService(db)
    created = service.sync_gaps_to_wishlist(series_id)
    return {"wishlist_items_created": created}


# === Smart Series ===

@router.post("/{series_id}/refresh")
def refresh_smart_series(
    series_id: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """Refresh a smart series membership."""
    series = db.query(Series).filter(Series.id == series_id).first()
    if not series:
        raise HTTPException(404, "Series not found")
    
    if series.series_type != SeriesType.SMART:
        raise HTTPException(400, "Not a smart series")
    
    service = SeriesService(db)
    changes = service.refresh_smart_series(series_id)
    
    return {"changes": changes}


# === Templates ===

@router.get("/templates")
def list_templates(
    category: str | None = None,
    canonical_only: bool = False,
    db: Session = Depends(get_db),
):
    """List available series templates."""
    query = db.query(SeriesTemplate).filter(SeriesTemplate.is_active == True)
    
    if category:
        query = query.filter(SeriesTemplate.category == category)
    
    if canonical_only:
        query = query.filter(SeriesTemplate.is_canonical == True)
    
    templates = query.order_by(SeriesTemplate.times_used.desc()).all()
    
    return {
        "items": [
            {
                "id": t.id,
                "name": t.name,
                "slug": t.slug,
                "description": t.description,
                "type": t.series_type.value,
                "category": t.category,
                "slot_count": t.slot_count,
                "difficulty": t.difficulty,
                "estimated_cost": {
                    "low": t.estimated_cost_low,
                    "high": t.estimated_cost_high,
                },
                "is_canonical": t.is_canonical,
                "times_used": t.times_used,
            }
            for t in templates
        ],
    }


@router.get("/templates/{template_id}")
def get_template(template_id: int, db: Session = Depends(get_db)):
    """Get template details including slot definitions."""
    template = db.query(SeriesTemplate).filter(SeriesTemplate.id == template_id).first()
    if not template:
        raise HTTPException(404, "Template not found")
    
    return {
        "id": template.id,
        "name": template.name,
        "description": template.description,
        "type": template.series_type.value,
        "category": template.category,
        "slot_count": template.slot_count,
        "template_data": template.template_data,
        "source_reference": template.source_reference,
        "estimated_cost": {
            "low": template.estimated_cost_low,
            "high": template.estimated_cost_high,
        },
    }


from sqlalchemy import func
from datetime import datetime
```

---

## Frontend Components

### Series Dashboard

```typescript
// pages/SeriesDashboard.tsx
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router-dom'
import { Progress } from '@/components/ui/progress'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { api } from '@/lib/api'

export function SeriesDashboard() {
  const { data: series } = useQuery({
    queryKey: ['series'],
    queryFn: () => api.get('/series').then(r => r.data),
  })
  
  return (
    <div className="container py-6">
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-3xl font-bold">My Series</h1>
        <Link to="/series/new">
          <Button>Create Series</Button>
        </Link>
      </div>
      
      {/* Summary cards */}
      <div className="grid grid-cols-4 gap-4 mb-8">
        <SummaryCard 
          title="Total Series" 
          value={series?.total || 0} 
        />
        <SummaryCard 
          title="Completed" 
          value={series?.items.filter(s => s.is_complete).length || 0}
          variant="success"
        />
        <SummaryCard 
          title="In Progress" 
          value={series?.items.filter(s => !s.is_complete && s.filled_count > 0).length || 0}
        />
        <SummaryCard 
          title="Not Started" 
          value={series?.items.filter(s => s.filled_count === 0).length || 0}
          variant="muted"
        />
      </div>
      
      {/* Series grid */}
      <div className="grid grid-cols-3 gap-6">
        {series?.items.map(s => (
          <SeriesCard key={s.id} series={s} />
        ))}
      </div>
    </div>
  )
}

function SeriesCard({ series }) {
  return (
    <Link to={`/series/${series.id}`}>
      <Card className="hover:shadow-lg transition-shadow">
        <CardHeader className="pb-2">
          <div className="flex justify-between items-start">
            <CardTitle className="text-lg">{series.name}</CardTitle>
            <Badge variant={series.is_complete ? "success" : "secondary"}>
              {series.type}
            </Badge>
          </div>
        </CardHeader>
        <CardContent>
          <div className="space-y-3">
            <Progress value={series.completion_percentage} />
            <div className="flex justify-between text-sm text-muted-foreground">
              <span>{series.filled_count} / {series.target_count}</span>
              <span>{Math.round(series.completion_percentage)}%</span>
            </div>
          </div>
        </CardContent>
      </Card>
    </Link>
  )
}
```

### Series Detail View

```typescript
// pages/SeriesDetail.tsx
import { useParams } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { DndContext, closestCenter } from '@dnd-kit/core'
import { SortableContext, rectSortingStrategy } from '@dnd-kit/sortable'
import { api } from '@/lib/api'

export function SeriesDetail() {
  const { id } = useParams()
  const queryClient = useQueryClient()
  
  const { data: series } = useQuery({
    queryKey: ['series', id],
    queryFn: () => api.get(`/series/${id}`).then(r => r.data),
  })
  
  const addCoinMutation = useMutation({
    mutationFn: ({ coinId, slotId }) => 
      api.post(`/series/${id}/coins/${coinId}`, null, { params: { slot_id: slotId } }),
    onSuccess: () => queryClient.invalidateQueries(['series', id]),
  })
  
  if (!series) return <Loading />
  
  return (
    <div className="container py-6">
      {/* Header */}
      <div className="flex justify-between items-start mb-8">
        <div>
          <h1 className="text-3xl font-bold">{series.name}</h1>
          <p className="text-muted-foreground mt-1">{series.description}</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild>
            <Link to={`/series/${id}/gaps`}>Gap Analysis</Link>
          </Button>
          <Button variant="outline" onClick={() => syncToWishlist()}>
            Sync to Wishlist
          </Button>
        </div>
      </div>
      
      {/* Stats */}
      <div className="grid grid-cols-5 gap-4 mb-8">
        <StatCard label="Completion" value={`${Math.round(series.stats.completion.percentage)}%`} />
        <StatCard label="Filled" value={`${series.stats.completion.filled}/${series.stats.completion.target}`} />
        <StatCard label="Total Value" value={formatCurrency(series.stats.value.total_value)} />
        <StatCard label="Gaps" value={series.stats.gaps.count} />
        <StatCard label="Budget Left" value={formatCurrency(series.stats.budget.remaining)} />
      </div>
      
      {/* Slot grid */}
      <DndContext collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
        <SortableContext items={series.slots.map(s => s.id)} strategy={rectSortingStrategy}>
          <div className="grid grid-cols-4 gap-4">
            {series.slots.map(slot => (
              <SlotCard
                key={slot.id}
                slot={slot}
                onAddCoin={(coinId) => addCoinMutation.mutate({ coinId, slotId: slot.id })}
              />
            ))}
          </div>
        </SortableContext>
      </DndContext>
    </div>
  )
}

function SlotCard({ slot, onAddCoin }) {
  const statusColors = {
    filled: 'bg-green-100 border-green-300',
    wanted: 'bg-yellow-100 border-yellow-300',
    empty: 'bg-gray-50 border-gray-200',
    upgrade: 'bg-blue-100 border-blue-300',
    not_targeted: 'bg-gray-100 border-gray-300 opacity-50',
  }
  
  return (
    <Card className={cn('border-2', statusColors[slot.status])}>
      <CardHeader className="p-3">
        <div className="flex justify-between items-center">
          <span className="font-medium">{slot.number}. {slot.name}</span>
          {slot.difficulty && (
            <Badge variant="outline">
              {'★'.repeat(Math.min(slot.difficulty, 5))}
            </Badge>
          )}
        </div>
      </CardHeader>
      <CardContent className="p-3 pt-0">
        {slot.coins.length > 0 ? (
          <div className="space-y-2">
            {slot.coins.map(c => (
              <CoinMiniCard key={c.id} coinId={c.id} isPrimary={c.is_primary} />
            ))}
          </div>
        ) : (
          <div className="text-center py-4">
            <p className="text-sm text-muted-foreground mb-2">
              {slot.rarity && <span className="capitalize">{slot.rarity}</span>}
            </p>
            <CoinSelector onSelect={onAddCoin} criteria={slot.match_criteria} />
          </div>
        )}
      </CardContent>
    </Card>
  )
}
```

---

## Integration Points

### Auto-assign on Coin Creation

```python
# In coin creation flow
def on_coin_created(coin: Coin, db: Session):
    """Check if new coin should be auto-added to any series."""
    service = SeriesService(db)
    
    # Check smart series
    smart_series = db.query(Series).filter(
        Series.series_type == SeriesType.SMART,
        Series.auto_update == True,
        Series.is_active == True,
    ).all()
    
    for series in smart_series:
        if series.smart_criteria:
            if _coin_matches_criteria(coin, series.smart_criteria):
                service.add_coin_to_series(series.id, coin.id)
    
    # Check for slot matches in structured series
    structured_series = db.query(Series).filter(
        Series.series_type.in_([SeriesType.CANONICAL, SeriesType.USER_DEFINED]),
        Series.is_active == True,
    ).all()
    
    for series in structured_series:
        suggested_slot = service.suggest_slot_for_coin(series.id, coin.id)
        if suggested_slot and suggested_slot.status == SlotStatus.WANTED:
            # Notify user of potential match
            create_notification(
                type="series_match",
                message=f"New coin may fit '{suggested_slot.name}' in {series.name}",
                data={"series_id": series.id, "slot_id": suggested_slot.id, "coin_id": coin.id},
            )
```

---

## Migration Script

```python
# migrations/add_series_tables.py
"""
Add series management tables.

Revision ID: series_001
"""

def upgrade():
    # Series table
    op.create_table(
        'series',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(100), unique=True, index=True),
        sa.Column('description', sa.Text()),
        sa.Column('series_type', sa.String(20), nullable=False),
        sa.Column('category', sa.String(50)),
        sa.Column('parent_id', sa.Integer(), sa.ForeignKey('series.id', ondelete='SET NULL')),
        sa.Column('sort_order', sa.Integer(), default=0),
        sa.Column('target_count', sa.Integer()),
        sa.Column('is_complete', sa.Boolean(), default=False),
        sa.Column('completion_date', sa.DateTime()),
        sa.Column('smart_criteria', sa.JSON()),
        sa.Column('auto_update', sa.Boolean(), default=False),
        sa.Column('display_mode', sa.String(20), default='grid'),
        sa.Column('cover_image_url', sa.String(500)),
        sa.Column('is_template', sa.Boolean(), default=False),
        sa.Column('is_canonical', sa.Boolean(), default=False),
        sa.Column('is_public', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_archived', sa.Boolean(), default=False),
        sa.Column('budget_total', sa.Float()),
        sa.Column('budget_spent', sa.Float(), default=0),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
    )
    
    # Series slots
    op.create_table(
        'series_slots',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('series_id', sa.Integer(), sa.ForeignKey('series.id', ondelete='CASCADE'), nullable=False),
        sa.Column('slot_number', sa.Integer(), nullable=False),
        sa.Column('slug', sa.String(50)),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('match_criteria', sa.JSON()),
        sa.Column('issuer_id', sa.Integer(), sa.ForeignKey('issuers.id')),
        sa.Column('mint_id', sa.Integer(), sa.ForeignKey('mints.id')),
        sa.Column('status', sa.String(20), default='empty'),
        sa.Column('priority', sa.Integer(), default=5),
        sa.Column('min_grade', sa.String(20)),
        sa.Column('target_grade', sa.String(20)),
        sa.Column('max_price', sa.Float()),
        sa.Column('difficulty', sa.Integer()),
        sa.Column('rarity_estimate', sa.String(20)),
        sa.Column('notes', sa.Text()),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('filled_at', sa.DateTime()),
    )
    
    # Series memberships
    op.create_table(
        'series_memberships',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('series_id', sa.Integer(), sa.ForeignKey('series.id', ondelete='CASCADE'), nullable=False),
        sa.Column('coin_id', sa.Integer(), sa.ForeignKey('coins.id', ondelete='CASCADE'), nullable=False),
        sa.Column('slot_id', sa.Integer(), sa.ForeignKey('series_slots.id', ondelete='SET NULL')),
        sa.Column('is_primary', sa.Boolean(), default=True),
        sa.Column('assignment_method', sa.String(20)),
        sa.Column('assigned_at', sa.DateTime()),
        sa.Column('meets_criteria', sa.Boolean(), default=True),
        sa.Column('upgrade_wanted', sa.Boolean(), default=False),
    )
    
    # Templates
    op.create_table(
        'series_templates',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('slug', sa.String(100), unique=True),
        sa.Column('description', sa.Text()),
        sa.Column('series_type', sa.String(20), nullable=False),
        sa.Column('category', sa.String(50)),
        sa.Column('difficulty', sa.Integer()),
        sa.Column('template_data', sa.JSON(), nullable=False),
        sa.Column('slot_count', sa.Integer()),
        sa.Column('estimated_cost_low', sa.Float()),
        sa.Column('estimated_cost_high', sa.Float()),
        sa.Column('times_used', sa.Integer(), default=0),
        sa.Column('source_reference', sa.String(200)),
        sa.Column('is_canonical', sa.Boolean(), default=False),
        sa.Column('is_verified', sa.Boolean(), default=False),
        sa.Column('is_active', sa.Boolean(), default=True),
    )
    
    # Wishlist
    op.create_table(
        'wishlist_items',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('description', sa.String(500), nullable=False),
        sa.Column('series_id', sa.Integer(), sa.ForeignKey('series.id', ondelete='SET NULL')),
        sa.Column('slot_id', sa.Integer(), sa.ForeignKey('series_slots.id', ondelete='SET NULL')),
        sa.Column('match_criteria', sa.JSON()),
        sa.Column('issuer_id', sa.Integer(), sa.ForeignKey('issuers.id')),
        sa.Column('priority', sa.Integer(), default=5),
        sa.Column('max_price', sa.Float()),
        sa.Column('min_grade', sa.String(20)),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_fulfilled', sa.Boolean(), default=False),
        sa.Column('fulfilled_by_coin_id', sa.Integer(), sa.ForeignKey('coins.id', ondelete='SET NULL')),
        sa.Column('alert_enabled', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime()),
    )
    
    # Indexes
    op.create_index('ix_series_type', 'series', ['series_type'])
    op.create_index('ix_series_slots_status', 'series_slots', ['status'])
    op.create_index('ix_series_memberships_coin', 'series_memberships', ['coin_id'])
    op.create_index('ix_wishlist_priority', 'wishlist_items', ['priority'])
```

---

## Summary

This comprehensive series feature adds:

| Component | Description |
|-----------|-------------|
| **7 Series Types** | Canonical, reference, dynastic, thematic, geographic, user-defined, smart |
| **Structured Slots** | Defined positions with criteria, difficulty, rarity ratings |
| **Smart Series** | Auto-populated based on filter criteria |
| **Completion Tracking** | Progress bars, percentage, filled counts |
| **Gap Analysis** | Missing items with difficulty assessment |
| **Wishlist Integration** | Auto-sync series gaps to wishlist |
| **Templates** | 30+ canonical series (Twelve Caesars, etc.) |
| **Budget Tracking** | Per-series budget with spent calculation |

**Effort Estimate:** 8-10 days

**Dependencies:**
- Controlled vocabulary (for issuer/mint linking)
- Reference normalization (for pattern matching)
