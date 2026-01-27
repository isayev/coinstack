from typing import Protocol, List, Optional
from dataclasses import dataclass
from decimal import Decimal
from datetime import date

@dataclass
class ImportedCoinRow:
    """Raw data from a row in the import file."""
    row_number: int
    raw_data: dict  # Original column -> value mapping
    
    # Normalized fields (best effort)
    category: Optional[str] = None
    metal: Optional[str] = None
    weight: Optional[Decimal] = None
    diameter: Optional[Decimal] = None
    issuer: Optional[str] = None
    grade: Optional[str] = None
    price: Optional[Decimal] = None
    date: Optional[date] = None
    references: Optional[List[dict]] = None

class ICollectionImporter(Protocol):
    def load(self, file_path: str) -> List[ImportedCoinRow]:
        """Parses the file and returns a list of rows."""
        ...
