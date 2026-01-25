from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from sqlalchemy.orm import Session
from src.application.commands.scrape_lot import ScrapeAuctionLotUseCase, ScrapeLotDTO
from src.application.commands.enrich_coin import EnrichCoinUseCase, EnrichCoinDTO
from src.domain.services.scraper_orchestrator import ScraperOrchestrator
from src.infrastructure.scrapers.mock_scraper import MockScraper
from src.infrastructure.scrapers.heritage.scraper import HeritageScraper
from src.infrastructure.scrapers.cng.scraper import CNGScraper
from src.infrastructure.scrapers.biddr.scraper import BiddrScraper
from src.infrastructure.scrapers.ebay.scraper import EbayScraper
from src.infrastructure.scrapers.agora.scraper import AgoraScraper

from src.infrastructure.persistence.database import get_db
from src.infrastructure.repositories.coin_repository import SqlAlchemyCoinRepository
from src.infrastructure.repositories.auction_data_repository import SqlAlchemyAuctionDataRepository

# In a real app, we'd inject real scrapers here
def get_scraper_orchestrator():
    return ScraperOrchestrator([
        HeritageScraper(),
        CNGScraper(),
        BiddrScraper(),
        EbayScraper(),
        AgoraScraper(),
        MockScraper() 
    ])

router = APIRouter(prefix="/api/v2/scrape", tags=["scrape"])

class ScrapeRequest(BaseModel):
    url: str

class EnrichRequest(BaseModel):
    coin_id: int
    url: Optional[str] = None

class ScrapeResponse(BaseModel):
    source: str
    lot_id: str
    url: str
    sale_name: Optional[str] = None
    lot_number: Optional[str] = None
    hammer_price: Optional[Decimal] = None
    issuer: Optional[str] = None
    grade: Optional[str] = None

@router.post("/lot", response_model=ScrapeResponse)
async def scrape_lot(
    request: ScrapeRequest,
    orchestrator: ScraperOrchestrator = Depends(get_scraper_orchestrator)
):
    use_case = ScrapeAuctionLotUseCase(orchestrator)
    try:
        result = await use_case.execute(ScrapeLotDTO(url=request.url))
        return ScrapeResponse(
            source=result.source,
            lot_id=result.lot_id,
            url=result.url,
            sale_name=result.sale_name,
            lot_number=result.lot_number,
            hammer_price=result.hammer_price,
            issuer=result.issuer,
            grade=result.grade
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/enrich", response_model=ScrapeResponse)
async def enrich_coin(
    request: EnrichRequest,
    db: Session = Depends(get_db),
    orchestrator: ScraperOrchestrator = Depends(get_scraper_orchestrator)
):
    coin_repo = SqlAlchemyCoinRepository(db)
    auction_repo = SqlAlchemyAuctionDataRepository(db)
    use_case = EnrichCoinUseCase(coin_repo, auction_repo, orchestrator)
    
    try:
        result = await use_case.execute(EnrichCoinDTO(coin_id=request.coin_id, url=request.url))
        return ScrapeResponse(
            source=result.source,
            lot_id=result.lot_id,
            url=result.url,
            sale_name=result.sale_name,
            lot_number=result.lot_number,
            hammer_price=result.hammer_price,
            issuer=result.issuer,
            grade=result.grade
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
