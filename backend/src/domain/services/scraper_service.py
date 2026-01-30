from typing import Protocol, Optional, TypeVar, Generic
from enum import Enum
from dataclasses import dataclass
from src.domain.auction import AuctionLot

T = TypeVar("T")

class ScrapeStatus(str, Enum):
    SUCCESS = "success"
    NOT_FOUND = "not_found"
    BLOCKED = "blocked"
    ERROR = "error"

@dataclass
class ScrapeResult(Generic[T]):
    status: ScrapeStatus
    data: Optional[T] = None
    error_message: Optional[str] = None

class IScraper(Protocol):
    """Interface for an auction scraper."""
    
    def can_handle(self, url: str) -> bool:
        """Checks if this scraper handles the given URL."""
        ...

    async def scrape(self, url: str) -> ScrapeResult[AuctionLot]:
        """Scrapes the URL and returns a ScrapeResult."""
        ...
