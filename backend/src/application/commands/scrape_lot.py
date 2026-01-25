from dataclasses import dataclass
from src.domain.repositories import ICoinRepository
from src.domain.services.scraper_orchestrator import ScraperOrchestrator
from src.domain.auction import AuctionLot

@dataclass
class ScrapeLotDTO:
    url: str

class ScrapeAuctionLotUseCase:
    """
    Use Case: Scrape data from a provided auction URL.
    
    This is a "pure" use case that just retrieves the data.
    It does not persist it to the database yet. That would be
    a separate 'EnrichCoin' or 'SaveAuctionData' use case.
    """
    
    def __init__(self, orchestrator: ScraperOrchestrator):
        self.orchestrator = orchestrator

    async def execute(self, dto: ScrapeLotDTO) -> AuctionLot:
        return await self.orchestrator.scrape(dto.url)
