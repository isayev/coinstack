from typing import Protocol, Optional, List
from src.domain.coin import Coin

class ICoinRepository(Protocol):
    def save(self, coin: Coin) -> Coin:
        """Saves a coin and returns the updated entity (with ID)."""
        ...

    def get_by_id(self, coin_id: int) -> Optional[Coin]:
        """Retrieves a coin by ID."""
        ...

    def get_all(self, skip: int = 0, limit: int = 100, sort_by: Optional[str] = None, sort_dir: str = "asc") -> List[Coin]:
        """Retrieves a list of coins with pagination and sorting."""
        ...
        
    def delete(self, coin_id: int) -> bool:
        """Deletes a coin by ID."""
        ...

    def count(self) -> int:
        """Returns the total number of coins."""
        ...
