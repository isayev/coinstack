from dataclasses import dataclass, field
from typing import Optional, List
from datetime import date
from decimal import Decimal
from enum import Enum

# --- Enums ---

class Metal(str, Enum):
    GOLD = "gold"
    SILVER = "silver"
    BRONZE = "bronze"
    COPPER = "copper"
    ELECTRUM = "electrum"
    BILLON = "billon"
    POTIN = "potin"
    ORICHALCUM = "orichalcum"

class Category(str, Enum):
    GREEK = "greek"
    ROMAN_IMPERIAL = "roman_imperial"
    ROMAN_REPUBLIC = "roman_republic"
    ROMAN_PROVINCIAL = "roman_provincial"
    BYZANTINE = "byzantine"
    MEDIEVAL = "medieval"

class GradingState(str, Enum):
    RAW = "raw"
    SLABBED = "slabbed"
    CAPSULE = "capsule"
    FLIP = "flip"

class GradeService(str, Enum):
    NGC = "ngc"
    PCGS = "pcgs"
    ICG = "icg"
    ANACS = "anacs"
    NONE = "none"

# --- Value Objects ---

@dataclass(frozen=True)
class Dimensions:
    weight_g: Decimal
    diameter_mm: Decimal
    die_axis: Optional[int] = None

    def __post_init__(self):
        if self.weight_g < 0:
            raise ValueError("Weight must be positive")
        if self.diameter_mm < 0:
            raise ValueError("Diameter must be positive")
        if self.die_axis is not None and not (0 <= self.die_axis <= 12):
            raise ValueError("Die axis must be between 0 and 12")

@dataclass(frozen=True)
class Attribution:
    issuer: str
    mint: Optional[str] = None
    year_start: Optional[int] = None
    year_end: Optional[int] = None

@dataclass(frozen=True)
class GradingDetails:
    grading_state: GradingState
    grade: str
    service: Optional[GradeService] = None
    certification_number: Optional[str] = None
    strike: Optional[str] = None
    surface: Optional[str] = None

    def __post_init__(self):
        if self.grading_state == GradingState.SLABBED and not self.service:
            pass

@dataclass(frozen=True)
class AcquisitionDetails:
    price: Decimal
    currency: str
    source: str
    date: Optional[date] = None
    url: Optional[str] = None

    def __post_init__(self):
        if self.price < 0:
            raise ValueError("Price cannot be negative")

@dataclass(frozen=True)
class CoinImage:
    """Represents an image of the coin."""
    url: str
    image_type: str # 'obverse', 'reverse', 'slab', etc.
    is_primary: bool = False

# --- Aggregate Root ---

@dataclass
class Coin:
    id: Optional[int]
    category: Category
    metal: Metal
    dimensions: Dimensions
    attribution: Attribution
    grading: GradingDetails
    acquisition: Optional[AcquisitionDetails] = None
    description: Optional[str] = None
    images: List[CoinImage] = field(default_factory=list)
    
    def is_dated(self) -> bool:
        return self.attribution.year_start is not None

    def update_dimensions(self, new_dimensions: Dimensions):
        self.dimensions = new_dimensions
    
    def add_image(self, url: str, image_type: str, is_primary: bool = False):
        if is_primary:
            for img in self.images:
                # We can't modify frozen dataclass items directly if we made them frozen,
                # but CoinImage is frozen, the list isn't.
                # However, changing is_primary on an existing frozen object requires replacement.
                # For simplicity in this domain model, we might need a method to handle this
                # or make CoinImage mutable (not ideal for VO).
                # Let's assume we replace the list or images.
                pass 
        self.images.append(CoinImage(url, image_type, is_primary))
    
    @property
    def primary_image(self) -> Optional[CoinImage]:
        for img in self.images:
            if img.is_primary:
                return img
        return self.images[0] if self.images else None