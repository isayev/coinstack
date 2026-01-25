from dataclasses import dataclass
from typing import List, Protocol, Optional, Any
from decimal import Decimal
from src.domain.coin import Coin

@dataclass(frozen=True)
class ExternalAuctionData:
    """Represents data from an external source (Heritage, CNG, etc)."""
    source: str
    lot_number: str
    grade: Optional[str] = None
    service: Optional[str] = None
    realized_price: Optional[Decimal] = None
    currency: Optional[str] = None
    description: Optional[str] = None
    
    # Attribution
    issuer: Optional[str] = None
    mint: Optional[str] = None
    year_start: Optional[int] = None
    year_end: Optional[int] = None
    
    # Physics
    weight_g: Optional[Decimal] = None
    diameter_mm: Optional[Decimal] = None
    die_axis: Optional[int] = None

@dataclass(frozen=True)
class Discrepancy:
    """Represents a difference between our data and external data."""
    field: str
    current_value: str
    auction_value: str
    confidence: float # 0.0 to 1.0
    source: str

class IAuditStrategy(Protocol):
    def audit(self, coin: Coin, auction_data: ExternalAuctionData) -> List[Discrepancy]:
        ...

class AuditEngine:
    def __init__(self, strategies: List[IAuditStrategy]):
        self.strategies = strategies

    def run(self, coin: Coin, auction_data: ExternalAuctionData) -> List[Discrepancy]:
        results = []
        for strategy in self.strategies:
            results.extend(strategy.audit(coin, auction_data))
        return results
