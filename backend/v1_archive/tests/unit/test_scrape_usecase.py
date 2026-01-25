import pytest
from src.application.commands.scrape_lot import ScrapeAuctionLotUseCase, ScrapeLotDTO
from src.domain.services.scraper_orchestrator import ScraperOrchestrator
from src.infrastructure.scrapers.mock_scraper import MockScraper

@pytest.mark.asyncio
async def test_scrape_lot_use_case():
    # Arrange
    mock_scraper = MockScraper()
    orchestrator = ScraperOrchestrator([mock_scraper])
    use_case = ScrapeAuctionLotUseCase(orchestrator)
    
    dto = ScrapeLotDTO(url="http://mock-auction.com/lot/123")

    # Act
    result = await use_case.execute(dto)

    # Assert
    assert result.source == "MockAuction"
    assert result.lot_id == "12345"
