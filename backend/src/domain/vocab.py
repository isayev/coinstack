from dataclasses import dataclass
from enum import Enum
from typing import Optional

class IssuerType(str, Enum):
    EMPEROR = "emperor"
    EMPRESS = "empress"
    CAESAR = "caesar"
    USURPER = "usurper"
    MAGISTRATE = "magistrate"
    KING = "king"
    OTHER = "other"

@dataclass
class Issuer:
    id: int
    canonical_name: str
    nomisma_id: str
    issuer_type: IssuerType
    reign_start: Optional[int] = None
    reign_end: Optional[int] = None

    def __post_init__(self):
        if self.reign_start is not None and self.reign_end is not None:
            if self.reign_start > self.reign_end:
                raise ValueError("Reign start cannot be after reign end")

    def is_active_in_year(self, year: int) -> bool:
        start = self.reign_start if self.reign_start is not None else float('-inf')
        end = self.reign_end if self.reign_end is not None else float('inf')
        return start <= year <= end

@dataclass
class Mint:
    id: int
    canonical_name: str
    nomisma_id: str
    active_from: Optional[int] = None
    active_to: Optional[int] = None

    def __post_init__(self):
        if self.active_from is not None and self.active_to is not None:
            if self.active_from > self.active_to:
                raise ValueError("Active start cannot be after active end")

    def is_active_in_year(self, year: int) -> bool:
        start = self.active_from if self.active_from is not None else float('-inf')
        end = self.active_to if self.active_to is not None else float('inf')
        return start <= year <= end
