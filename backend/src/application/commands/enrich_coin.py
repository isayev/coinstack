from dataclasses import dataclass
from typing import Optional
from src.domain.repositories import ICoinRepository
from src.infrastructure.repositories.auction_data_repository import SqlAlchemyAuctionDataRepository
from src.domain.services.scraper_orchestrator import ScraperOrchestrator
from src.domain.auction import AuctionLot

@dataclass
class EnrichCoinDTO:
    coin_id: int
    url: Optional[str] = None # Override URL needed? Usually takes from coin.

class EnrichCoinUseCase:
    """
    Use Case: Scrape auction data for a coin and persist it.
    
    1. Resolve URL (from input or Coin record).
    2. Scrape data.
    3. Update/Create AuctionData record linked to the Coin.
    """
    
    def __init__(
        self, 
        coin_repo: ICoinRepository,
        auction_repo: SqlAlchemyAuctionDataRepository,
        orchestrator: ScraperOrchestrator
    ):
        self.coin_repo = coin_repo
        self.auction_repo = auction_repo
        self.orchestrator = orchestrator

    async def execute(self, dto: EnrichCoinDTO) -> AuctionLot:
        # 1. Get Coin
        coin = self.coin_repo.get_by_id(dto.coin_id)
        if not coin:
            raise ValueError(f"Coin {dto.coin_id} not found")
            
        # 2. Determine URL
        url = dto.url
        if not url:
            if coin.acquisition and coin.acquisition.url:
                url = coin.acquisition.url
        
        if not url:
            raise ValueError(f"No acquisition URL found for Coin {dto.coin_id}")
            
        # 3. Scrape
        auction_lot = await self.orchestrator.scrape(url)
        if not auction_lot:
             raise RuntimeError(f"Failed to scrape {url}")
             
        # 4. Persist
        self.auction_repo.upsert(auction_lot, coin_id=dto.coin_id)
        
        return auction_lot
