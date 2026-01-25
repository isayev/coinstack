from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

class SeriesType(str, Enum):
    CANONICAL = "canonical"
    REFERENCE = "reference"
    DYNASTIC = "dynastic"
    THEMATIC = "thematic"
    GEOGRAPHIC = "geographic"
    TEMPORAL = "temporal"
    USER_DEFINED = "user_defined"
    SMART = "smart"

class SlotStatus(str, Enum):
    EMPTY = "empty"
    WANTED = "wanted"
    FILLED = "filled"
    UPGRADE_WANTED = "upgrade"
    NOT_TARGETED = "not_targeted"
    MULTIPLE = "multiple"

@dataclass
class SeriesSlot:
    id: int
    series_id: int
    slot_number: int
    name: str
    description: Optional[str] = None
    status: SlotStatus = SlotStatus.EMPTY
    coin_id: Optional[int] = None
    priority: int = 5

@dataclass
class Series:
    id: int
    name: str
    series_type: SeriesType
    slug: Optional[str] = None
    description: Optional[str] = None
    slots: List[SeriesSlot] = field(default_factory=list)
    target_count: Optional[int] = None
    is_complete: bool = False

    @property
    def completion_percentage(self) -> float:
        if not self.target_count or self.target_count <= 0:
            return 0.0
        filled = sum(1 for s in self.slots if s.status == SlotStatus.FILLED)
        return (filled / self.target_count) * 100
